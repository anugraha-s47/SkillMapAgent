
import json
import os
import re

import requests
from dotenv import load_dotenv
from langchain_core.messages import RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import trim_messages
from langchain.agents import create_agent
from langchain.agents.middleware import before_model
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch


# ============================================================
# 1. Load and validate API keys
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing from .env")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY is missing from .env")

if not RAPIDAPI_KEY:
    raise ValueError("RAPIDAPI_KEY is missing from .env")


# ============================================================
# 2. Initialize the language model
# ============================================================

model = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0,
)


# ============================================================
# 3. Tavily skill-demand research tool
# ============================================================

skill_demand_tool = TavilySearch(
    max_results=3,
    search_depth="basic",
    include_raw_content=False,
    tavily_api_key=TAVILY_API_KEY,
)


# ============================================================
# 4. Store the latest job results for follow-up questions
# ============================================================

# These dictionaries remain in memory while this Python process runs.
# Each conversation thread gets its own latest job list.
latest_jobs_by_thread = {}


# ============================================================
# 5. Job-search tool
# ============================================================

@tool
def search_jobs(skill: str, location: str) -> str:
    """
    Search for internships, fresher jobs, and experienced jobs.
    Classify listings, remove duplicates, and preserve application links.
    Return compact structured JSON to reduce LLM token usage.
    """

    url = "https://jsearch.p.rapidapi.com/search-v2"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }

    search_queries = [
        (
            f"{skill} internship intern jobs in {location}",
            "Internship search",
        ),
        (
            f"{skill} fresher entry level graduate trainee jobs in {location}",
            "Fresher search",
        ),
        (
            f"{skill} experienced senior developer jobs in {location}",
            "Experienced search",
        ),
    ]

    all_jobs = []
    seen_jobs = set()
    errors = []

    senior_pattern = re.compile(
        r"\b(?:senior|sr\.?|lead|principal|staff engineer|architect|"
        r"engineering manager|tech lead)\b",
        re.IGNORECASE,
    )

    fresher_pattern = re.compile(
        r"\b(?:fresher|freshers|entry[\s-]?level|graduate trainee|"
        r"trainee|new grad|campus hire)\b",
        re.IGNORECASE,
    )

    internship_pattern = re.compile(
        r"\b(?:intern|internship)\b",
        re.IGNORECASE,
    )

    for query, search_type in search_queries:
        params = {
            "query": query,
            "page": "1",
            "country": "in",
        }

        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ERROR":
                errors.append({
                    "search": search_type,
                    "error": data.get(
                        "message",
                        "JSearch API error",
                    ),
                })
                continue

            payload = data.get("data", [])

            if isinstance(payload, dict):
                jobs = payload.get("jobs", [])
            elif isinstance(payload, list):
                jobs = payload
            else:
                jobs = []

            for job in jobs:
                title = job.get("job_title") or "Title not provided"
                title_lower = title.lower()

                experience = (
                    job.get("job_required_experience") or {}
                )

                if not isinstance(experience, dict):
                    experience = {}

                months = experience.get(
                    "required_experience_in_months"
                )

                no_experience = experience.get(
                    "no_experience_required"
                )

                apply_link = job.get("job_apply_link")
                company = job.get("employer_name") or "Not specified"

                job_location = (
                    job.get("job_location")
                    or job.get("job_city")
                    or "Not specified"
                )

                # Deduplicate using the application link where possible.
                if isinstance(apply_link, str) and apply_link.strip():
                    dedupe_key = apply_link.strip().lower()
                else:
                    dedupe_key = (
                        title_lower,
                        company.lower(),
                        job_location.lower(),
                    )

                if dedupe_key in seen_jobs:
                    continue

                seen_jobs.add(dedupe_key)

                # Preserve the original experience classification logic.
                if senior_pattern.search(title):
                    label = "Experienced"

                elif internship_pattern.search(title):
                    label = "Internship"

                elif no_experience is True:
                    label = "Fresher / Entry-level"

                elif (
                    isinstance(months, (int, float))
                    and not isinstance(months, bool)
                    and months >= 0
                ):
                    label = (
                        "Fresher / Entry-level"
                        if months <= 12
                        else "Experienced"
                    )

                elif fresher_pattern.search(title):
                    label = "Fresher / Entry-level"

                else:
                    label = "Experience not specified"

                # Keep the fields needed for display and follow-ups.
                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": job_location,
                    "experience_label": label,
                    "required_experience": experience,
                    "required_experience_months": months,
                    "no_experience_required": no_experience,
                    "employment_type": (
                        job.get("job_employment_type")
                        or "Not specified"
                    ),
                    "posted_date": (
                        job.get("job_posted_at")
                        or job.get(
                            "job_posted_at_datetime_utc"
                        )
                        or "Not specified"
                    ),
                    "apply_link": apply_link,
                    "search_type": search_type,
                })

        except requests.RequestException as error:
            details = (
                error.response.text[:300]
                if error.response is not None
                else ""
            )

            errors.append({
                "search": search_type,
                "error": str(error),
                "details": details,
            })

        except (ValueError, TypeError) as error:
            errors.append({
                "search": search_type,
                "error": (
                    f"Could not process API response: {error}"
                ),
            })

    # Return compact JSON to the model.
    # The full job records are retained separately by run_skillmap_agent.
    compact_jobs = []

    for job in all_jobs:
        compact_jobs.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "experience_label": job["experience_label"],
            "required_experience_months": (
                job["required_experience_months"]
            ),
            "no_experience_required": (
                job["no_experience_required"]
            ),
            "employment_type": job["employment_type"],
            "posted_date": job["posted_date"],
            "apply_link": job["apply_link"],
            "search_type": job["search_type"],
        })

    return json.dumps({
        "source": "JSearch API",
        "total_returned": len(compact_jobs),
        "jobs": compact_jobs,
        "search_errors": errors,
    }, ensure_ascii=False)


# ============================================================
# 6. Agent instructions
# ============================================================

system_prompt = """
You are SkillMap Agent, an AI career research assistant.

RESPONSIBILITIES:
1. Research demand for technical skills.
2. Explain related skills and career opportunities.
3. Find job openings using search_jobs.
4. Provide application links when available.

AVAILABLE TOOLS:
- tavily_search: Research industry trends and skill demand.
- search_jobs: Find job listings through JSearch.

TOOL SELECTION:
1. Use tavily_search for skill demand and market trends.
2. Use search_jobs for jobs, openings, vacancies, and internships.
3. Use both tools when the user requests both skill demand and jobs.
4. Do not answer job-search requests using only general web research.
5. Never invent tools or claim a tool succeeded when it failed.
6. Explain tool failures honestly.

JOB CLASSIFICATION:
1. Prioritize Fresher / Entry-level and Internship for fresher requests.
2. Prioritize Internship for internship requests.
3. Prioritize Experienced for senior and experienced requests.
4. Show all available categories when no experience level is specified.
5. Do not claim that jobs match a category unless the data supports it.
6. Prioritize the requested location.
7. Separate remote or unspecified locations where relevant.

JOB DATA RELIABILITY:
1. Preserve original titles, companies, locations, dates, and links.
2. Never invent salaries, requirements, links, or posting dates.
3. If a link is missing, say "Link not provided."
4. Do not claim a job is active without supporting evidence.
5. Distinguish API-provided experience from title-based clues.
6. If search_errors is not empty, disclose the affected searches.
7. If no jobs are returned, report that clearly.

CONVERSATION MEMORY:
1. Use recent conversation context for follow-up questions.
2. For "Tell me about Job 2", explain the selected job only.
3. Do not repeat the entire job list for a job-detail question.
4. Use only the job information supplied in the conversation.
5. Do not invent missing details.
6. If the user provides a specific job record, use that record as the
   primary source for the answer.
7. When the user starts a new search, do not confuse it with an older one.

RESPONSE STYLE:
1. Use beginner-friendly English and clear headings.
2. Group jobs by experience_label.
3. Include title, company, location, experience, employment type,
   posting date, and application link when available.
4. Distinguish verified facts from uncertain information.
5. Include source URLs for skill-demand research when available.
6. Never claim that Python filtered results unless the filtering
   was actually performed.

IMPLEMENTATION LIMITATION:
Search results may contain multiple experience categories.
Do not claim a job matches a requested category unless the data supports it.
"""


# ============================================================
# 7. Trim conversation history before model calls
# ============================================================


@before_model
def limit_conversation_history(state, runtime):
    messages = state.get("messages", [])

    if not messages:
        return None

    # Keep only the most recent 8 messages.
    recent_messages = messages[-8:]

    # Start at a human message to avoid beginning with
    # an orphaned AI or tool response.
    while recent_messages and recent_messages[0].type != "human":
        recent_messages = recent_messages[1:]

    if not recent_messages:
        return None

    # Replace the old message history with the smaller history.
    return {
        "messages": [
            RemoveMessage(id=REMOVE_ALL_MESSAGES),
            *recent_messages,
        ]
    }


# ============================================================
# 8. Create the agent and short-term memory
# ============================================================

checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[skill_demand_tool, search_jobs],
    system_prompt=system_prompt,
    checkpointer=checkpointer,
    middleware=[limit_conversation_history],
)


# ============================================================
# 9. Extract job results from the tool response
# ============================================================

def extract_job_results(response: dict):
    """Extract job records from the search_jobs tool message."""

    for message in response.get("messages", []):
        if getattr(message, "name", "") != "search_jobs":
            continue

        content = getattr(message, "content", "")

        if not isinstance(content, str):
            continue

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            continue

        if isinstance(data, dict) and isinstance(data.get("jobs"), list):
            return data["jobs"]

    return []


# ============================================================
# 10. Format job listings
# ============================================================

def format_job_results(jobs, skill="Technical"):
    """Format listings with experience information and application links."""

    if not jobs:
        return "The job search returned no job listings."

    groups = {
        "Fresher / Entry-level": [],
        "Internship": [],
        "Experienced": [],
        "Experience not specified": [],
    }

    for job in jobs:
        label = job.get(
            "experience_label",
            "Experience not specified",
        )

        if label not in groups:
            label = "Experience not specified"

        groups[label].append(job)

    lines = [f"# {skill} Job Search Results"]

    for label, grouped_jobs in groups.items():
        if not grouped_jobs:
            continue

        lines.append(f"\n## {label}")

        for index, job in enumerate(grouped_jobs, start=1):
            months = job.get("required_experience_months")
            no_experience = job.get("no_experience_required")
            title = job.get("title") or "Not specified"
            apply_link = job.get("apply_link") or "Link not provided"

            if no_experience is True:
                experience_text = "No experience required (API data)"

            elif (
                isinstance(months, (int, float))
                and not isinstance(months, bool)
            ):
                experience_text = f"{months} months (API data)"

            else:
                experience = job.get("required_experience") or {}

                if not isinstance(experience, dict):
                    experience = {}

                experience_text = (
                    experience.get("experience_text")
                    or "Not specified by API"
                )

                if experience_text == "Not specified by API":
                    pattern = (
                        r"\b\d+\s*(?:-|–|—|to)\s*\d+\s*"
                        r"(?:years?|yrs?\.?)\b"
                        r"|\b\d+\s*\+\s*(?:years?|yrs?\.?)\b"
                        r"|\b\d+\s*(?:years?|yrs?\.?)\b"
                    )

                    match = re.search(
                        pattern,
                        title,
                        re.IGNORECASE,
                    )

                    if not match and apply_link != "Link not provided":
                        match = re.search(
                            pattern,
                            apply_link.replace("-", " "),
                            re.IGNORECASE,
                        )

                    if match:
                        experience_text = (
                            f"{match.group(0)} "
                            "(title/URL clue; verify in job description)"
                        )

            lines.extend([
                f"\n### {index}. {title}",
                f"- Company: {job.get('company') or 'Not specified'}",
                f"- Location: {job.get('location') or 'Not specified'}",
                f"- Required experience: {experience_text}",
                (
                    "- Employment type: "
                    f"{job.get('employment_type') or 'Not specified'}"
                ),
                (
                    "- Posting date: "
                    f"{job.get('posted_date') or 'Not specified'}"
                ),
                f"- Application link: {apply_link}",
            ])

    lines.append(
        "\n---\n"
        "Note: Experience inferred from a title or URL is only a clue. "
        "Check the original job description before applying."
    )

    return "\n".join(lines)


# ============================================================
# 11. Identify job follow-up questions
# ============================================================

def get_job_number(query: str):
    """Extract a job number from queries such as 'Tell me about Job 2'."""

    match = re.search(
        r"\bjob\s*#?\s*(\d+)\b",
        query,
        re.IGNORECASE,
    )

    if match:
        return int(match.group(1))

    ordinal_numbers = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
    }

    for word, number in ordinal_numbers.items():
        if re.search(rf"\bthe {word} one\b", query, re.IGNORECASE):
            return number

    return None


def is_job_follow_up(query: str):
    """Identify follow-up questions about a previously listed job."""

    query_lower = query.lower().strip()

    follow_up_terms = [
        "tell me about job",
        "details about job",
        "more about job",
        "explain job",
        "that job",
        "this job",
        "the second one",
        "the first one",
        "the third one",
        "the fourth one",
        "the fifth one",
        "that position",
        "this position",
    ]

    return (
        get_job_number(query) is not None
        or any(term in query_lower for term in follow_up_terms)
    )


# ============================================================
# 12. Run the agent with memory
# ============================================================

def run_skillmap_agent(
    user_query: str,
    thread_id: str = "skillmap-terminal",
) -> str:
    """Run SkillMap Agent with memory and reduced token usage."""

    query_lower = user_query.lower().strip()

    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }

    # --------------------------------------------------------
    # A. Handle job-detail follow-ups using saved job records.
    # --------------------------------------------------------

    if is_job_follow_up(user_query):
        saved_jobs = latest_jobs_by_thread.get(thread_id, [])
        job_number = get_job_number(user_query)

        if saved_jobs and job_number is not None:
            if 1 <= job_number <= len(saved_jobs):
                selected_job = saved_jobs[job_number - 1]

                # Send only the selected job to the model, not the
                # entire previous job-search result.
                follow_up_prompt = (
                    f"The user asks: {user_query}\n\n"
                    "Explain the following selected job. Use only the "
                    "provided facts. Do not invent responsibilities, "
                    "salary, requirements, or hiring status. If a detail "
                    "is missing, say it is not provided. Include the "
                    "application link when available.\n\n"
                    "Selected job record:\n"
                    f"{json.dumps(selected_job, ensure_ascii=False)}"
                )

                response = agent.invoke(
                    {
                        "messages": [
                            {
                                "role": "user",
                                "content": follow_up_prompt,
                            }
                        ]
                    },
                    config=config,
                )

                messages = response.get("messages", [])

                if messages:
                    content = getattr(messages[-1], "content", "")

                    if isinstance(content, str):
                        return content

                    return str(content)

                return "The agent returned no messages."

            return (
                f"Job {job_number} is not available in the latest "
                f"saved list, which contains {len(saved_jobs)} jobs. "
                "Please run a new search or choose a valid job number."
            )

        # For pronoun-based follow-ups, use conversation memory.
        if not saved_jobs:
            return (
                "I don't have a saved job list for this conversation. "
                "Please search for jobs first, then ask about a job number."
            )

    # --------------------------------------------------------
    # B. Run normal skill-demand or job-search requests.
    # --------------------------------------------------------

    response = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": user_query,
                }
            ]
        },
        config=config,
    )

    messages = response.get("messages", [])

    if not messages:
        return "The agent returned no messages."

    # Determine whether this is a new job-search request.
    job_terms = [
        "job",
        "jobs",
        "hiring",
        "vacancy",
        "vacancies",
        "opening",
        "openings",
        "internship",
        "internships",
        "intern",
        "career opportunities",
    ]

    is_job_query = any(
        term in query_lower
        for term in job_terms
    )

    # Return ordinary skill-demand answers directly.
    if not is_job_query:
        content = getattr(messages[-1], "content", "")

        if isinstance(content, str):
            return content

        return str(content)

    # Extract listings from the search tool response.
    job_results = extract_job_results(response)

    if not job_results:
        content = getattr(messages[-1], "content", "")

        if isinstance(content, str) and content.strip():
            return content

        return (
            "No job listings were returned. Try another keyword "
            "or location."
        )

    # --------------------------------------------------------
    # C. Filter experience categories as before.
    # --------------------------------------------------------

    internship_requested = any(
        term in query_lower
        for term in ["internship", "internships", "intern"]
    )

    senior_requested = any(
        term in query_lower
        for term in [
            "senior",
            "experienced",
            "experience",
            "mid-level",
            "mid level",
            "lead developer",
            "principal developer",
        ]
    )

    fresher_requested = any(
        term in query_lower
        for term in [
            "fresher",
            "freshers",
            "entry-level",
            "entry level",
            "graduate",
            "new grad",
            "campus placement",
        ]
    )

    if internship_requested:
        category_name = "Internship"

        filtered_jobs = [
            job for job in job_results
            if job.get("experience_label") == category_name
        ]

    elif senior_requested:
        category_name = "Experienced"

        filtered_jobs = [
            job for job in job_results
            if job.get("experience_label") == category_name
        ]

    elif fresher_requested:
        category_name = "Fresher / Entry-level"

        filtered_jobs = [
            job for job in job_results
            if job.get("experience_label") == category_name
        ]

    else:
        category_name = "All experience categories"
        filtered_jobs = job_results

    if not filtered_jobs:
        return (
            f"No jobs classified as '{category_name}' were found "
            "in the returned search results. This does not prove "
            "that no matching jobs exist. Try another keyword or location."
        )

    # Save the displayed job list for follow-up questions.
    latest_jobs_by_thread[thread_id] = filtered_jobs

    # Extract the requested skill for the heading.
    skill_match = re.search(
        r"\b(?:for|in)\s+([a-zA-Z0-9+#. -]+)",
        user_query,
        re.IGNORECASE,
    )

    skill_name = (
        skill_match.group(1).strip()
        if skill_match
        else "Technical"
    )

    return format_job_results(filtered_jobs, skill=skill_name)


# ============================================================
# 13. Interactive terminal application
# ============================================================

if __name__ == "__main__":
    print("SkillMap Agent started. Type 'exit' to stop.\n")

    while True:
        user_query = input(
            "Ask about skills and jobs (or type 'exit'): "
        ).strip()

        if user_query.lower() == "exit":
            print("SkillMap Agent stopped. Goodbye!")
            break

        if not user_query:
            print("Please enter a question.")
            continue

        try:
            result = run_skillmap_agent(user_query)

            print("\nSkillMap Agent:\n")
            print(result)
            print("\n" + "-" * 60 + "\n")

        except Exception as error:
            print(f"\nAn error occurred: {error}\n")

