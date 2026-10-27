
import html
import re

import streamlit as st

from main import run_skillmap_agent


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="SkillMap AI",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# 2. GLOBAL DESIGN SYSTEM
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --bg: #11131c;
        --surface: #1c2030;
        --surface-2: #23283a;
        --border: #30374a;
        --text: #f5f6fc;
        --muted: #a3abc0;
        --purple: #9867ff;
        --blue: #6289ff;
        --green: #78d6ad;
    }

    /* Application background */
    .stApp {
        background:
            radial-gradient(
                ellipse at 10% 0%,
                rgba(115, 75, 205, 0.13),
                transparent 35%
            ),
            var(--bg);
        color: var(--text);
    }

    /* Shared page alignment */
    .block-container {
        max-width: 1450px;
        width: 100%;
        padding: 2rem 2.4rem 7rem;
        margin: 0 auto;
        box-sizing: border-box;
    }

    /* Typography */
    h1, h2, h3, h4 {
        color: var(--text) !important;
        letter-spacing: -0.4px;
    }

    h1 {
        font-size: clamp(1.9rem, 3vw, 2.6rem) !important;
        font-weight: 750 !important;
    }

    h2 {
        font-size: 1.55rem !important;
        font-weight: 720 !important;
    }

    h3 {
        font-size: 1.18rem !important;
        font-weight: 650 !important;
    }

    p, li {
        color: #e0e4ef;
        line-height: 1.75;
    }

    .subtitle {
        color: var(--muted);
        font-size: 1rem;
        margin-top: -0.55rem;
        margin-bottom: 1.35rem;
    }

    .muted-text {
        color: var(--muted);
    }

    /* Small brand label */
    .brand-label {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #c9b6ff;
        background: rgba(152, 103, 255, 0.11);
        border: 1px solid rgba(152, 103, 255, 0.25);
        border-radius: 30px;
        padding: 0.42rem 0.85rem;
        font-size: 0.84rem;
        font-weight: 650;
        margin-bottom: 1rem;
    }

    /* Buttons */
    .stButton > button {
        min-height: 45px;
        padding: 0.65rem 1rem;
        border-radius: 11px;
        border: 1px solid var(--border);
        background: var(--surface);
        color: var(--text);
        font-weight: 600;
        transition: all 0.2s ease;
    }

    .stButton > button:hover {
        border-color: var(--purple);
        background: var(--surface-2);
        color: white;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(
            110deg,
            var(--purple),
            var(--blue)
        );
        border: none;
        color: white;
    }

    /* Home feature cards */
    .feature-card {
        min-height: 210px;
        background: linear-gradient(
            145deg,
            #22263a,
            #191d2a
        );
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1.5rem;
        margin: 0.3rem 0 1rem;
        box-sizing: border-box;
    }

    .feature-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 14px;
        background: rgba(152, 103, 255, 0.17);
        font-size: 1.5rem;
        margin-bottom: 1rem;
    }

    .feature-title {
        font-size: 1.22rem;
        color: var(--text);
        font-weight: 720;
        margin-bottom: 0.45rem;
    }

    .feature-description {
        color: var(--muted);
        font-size: 0.96rem;
        line-height: 1.65;
    }

    /* Chat history messages */
    [data-testid="stChatMessage"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1rem 1.25rem;
        margin: 0.9rem 0;
        width: 100%;
        box-sizing: border-box;
        overflow-wrap: anywhere;
    }

    /* Tables in Skill Demand results */
    [data-testid="stChatMessage"] table {
        display: block;
        width: 100%;
        overflow-x: auto;
        border-collapse: collapse;
    }

    [data-testid="stChatMessage"] th {
        background: #282d40;
        color: #e5dcff;
        text-align: left;
        padding: 0.85rem;
        border-bottom: 1px solid var(--border);
    }

    [data-testid="stChatMessage"] td {
        padding: 0.8rem;
        border-bottom: 1px solid var(--border);
        vertical-align: top;
    }

    [data-testid="stChatMessage"] tr:hover td {
        background: rgba(152, 103, 255, 0.05);
    }

    /* Search input */
    [data-testid="stChatInput"] {
        width: 100%;
        max-width: 100%;
    }

    [data-testid="stChatInput"] > div {
        background: #222635;
        border: 1px solid #45405f;
        border-radius: 13px;
    }

    [data-testid="stChatInput"] textarea {
        font-size: 1rem !important;
    }

    [data-testid="stBottom"] {
        background: rgba(17, 19, 28, 0.97);
    }

    [data-testid="stBottom"] > div {
        width: 100%;
        max-width: 1450px;
        margin: 0 auto;
        padding-left: 2.4rem;
        padding-right: 2.4rem;
        box-sizing: border-box;
    }

    /* Job cards */
    .job-card {
        background: linear-gradient(
            145deg,
            #222638,
            #1a1e2c
        );
        border: 1px solid var(--border);
        border-radius: 17px;
        padding: 1.35rem 1.5rem;
        margin: 1rem 0;
        width: 100%;
        box-sizing: border-box;
        transition: border-color 0.2s ease;
    }

    .job-card:hover {
        border-color: #8064d8;
    }

    .job-topline {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .job-title {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 720;
        line-height: 1.5;
        overflow-wrap: anywhere;
    }

    .job-company {
        color: #b9a5ff;
        font-size: 0.98rem;
        margin: 0.35rem 0 0.9rem;
    }

    .job-tag {
        display: inline-block;
        color: #d7c8ff;
        background: #32284f;
        border: 1px solid #49376c;
        border-radius: 30px;
        padding: 0.3rem 0.7rem;
        font-size: 0.8rem;
        white-space: nowrap;
        margin-bottom: 0.7rem;
    }

    .job-details {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.9rem 1.5rem;
        margin: 1rem 0;
    }

    .job-detail {
        color: #e0e4ef;
        font-size: 0.94rem;
        overflow-wrap: anywhere;
    }

    .job-label {
        display: block;
        color: var(--muted);
        font-size: 0.82rem;
        margin-bottom: 0.2rem;
    }

    .job-skills {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.8rem 0 1rem;
    }

    .skill-chip {
        display: inline-block;
        background: #252f40;
        border: 1px solid #344357;
        color: #c4dff2;
        border-radius: 25px;
        padding: 0.35rem 0.7rem;
        font-size: 0.82rem;
    }

    .apply-link {
        display: inline-block;
        background: linear-gradient(
            110deg,
            var(--purple),
            var(--blue)
        );
        color: white !important;
        text-decoration: none !important;
        padding: 0.7rem 1.1rem;
        border-radius: 10px;
        font-weight: 650;
        margin-top: 0.3rem;
    }

    .apply-link:hover {
        filter: brightness(1.12);
    }

    /* Section divider */
    .section-divider {
        border: none;
        border-top: 1px solid var(--border);
        margin: 1.4rem 0;
    }

    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .block-container {
            padding: 1.3rem 1rem 7rem;
        }

        [data-testid="stBottom"] > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .feature-card {
            min-height: auto;
        }

        .job-card {
            padding: 1rem;
        }

        .job-details {
            grid-template-columns: 1fr;
        }

        .job-topline {
            display: block;
        }

        [data-testid="stChatMessage"] {
            padding: 0.85rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. SESSION STATE
# =========================================================

if "selected_mode" not in st.session_state:
    st.session_state.selected_mode = None

if "messages" not in st.session_state:
    st.session_state.messages = {
        "skill_demand": [],
        "job_search": [],
    }


# =========================================================
# 4. JOB RESULT PARSER
# Supports the Markdown output from main.py
# =========================================================

def parse_job_results(result):
    jobs = []
    current_category = "Job"
    current_job = None

    for raw_line in result.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        # Category headings, e.g. Internship or Experienced
        if line.startswith("#"):
            heading = re.sub(r"^#+\s*", "", line).strip()
            if heading:
                current_category = heading
            continue

        # Numbered job heading, e.g. 1. **Title — Company**
        title_match = re.match(
            r"^\d+\.\s+\*\*(.*?)\*\*",
            line,
        )

        # Also accept numbered titles without Markdown bold.
        if not title_match:
            title_match = re.match(
                r"^\d+\.\s+(.+?)\s*$",
                line,
            )

        if title_match:
            if current_job:
                jobs.append(current_job)

            title_text = title_match.group(1).strip()
            title_text = re.sub(r"\s*\[.*?\]\(.*?\)", "", title_text)
            title_text = re.sub(r"\s+🔗.*$", "", title_text).strip()

            parts = re.split(
                r"\s+[—–]\s+",
                title_text,
                maxsplit=1,
            )

            current_job = {
                "title": parts[0].strip(),
                "company": parts[1].strip() if len(parts) > 1 else "",
                "category": current_category,
                "location": "Not specified",
                "experience": "Not specified",
                "employment": "Not specified",
                "posted": "Not specified",
                "url": "",
                "skills": [],
            }
            continue

        if current_job is None:
            continue

        # Remove bullet markers and Markdown formatting.
        clean_line = re.sub(r"^[-*•]\s*", "", line).strip()
        clean_line = clean_line.replace("**", "").replace("__", "")

        # Company
        if clean_line.lower().startswith("company:"):
            current_job["company"] = clean_line.split(":", 1)[1].strip()

        # Location
        elif clean_line.lower().startswith("location:"):
            current_job["location"] = clean_line.split(":", 1)[1].strip()

        # Experience
        elif clean_line.lower().startswith("required experience:"):
            current_job["experience"] = clean_line.split(":", 1)[1].strip()

        elif clean_line.lower().startswith("experience:"):
            current_job["experience"] = clean_line.split(":", 1)[1].strip()

        # Employment type
        elif clean_line.lower().startswith("employment type:"):
            current_job["employment"] = clean_line.split(":", 1)[1].strip()

        # Posting date
        elif clean_line.lower().startswith("posting date:"):
            current_job["posted"] = clean_line.split(":", 1)[1].strip()

        # Application URL
        elif clean_line.lower().startswith("application link:"):
            match = re.search(r"https?://\S+", clean_line)
            if match:
                current_job["url"] = match.group(0).rstrip(").,]")

        # Optional skills list if your output contains one.
        elif clean_line.lower().startswith("skills:"):
            skills_text = clean_line.split(":", 1)[1]
            current_job["skills"] = [
                skill.strip()
                for skill in re.split(r"[,|]", skills_text)
                if skill.strip()
            ]

    if current_job:
        jobs.append(current_job)

    return jobs


# =========================================================
# 5. JOB CARD RENDERER
# =========================================================

def render_job_cards(result, user_query):
    jobs = parse_job_results(result)

    # If the output format does not match the parser,
    # preserve the original agent answer.
    if not jobs:
        st.markdown(result)
        return

    st.markdown("## Matching Jobs")
    st.caption(f"{len(jobs)} listing(s) returned by the search tool.")

    for index, job in enumerate(jobs, start=1):
        title = html.escape(job["title"])
        company = html.escape(
            job["company"] or "Company not specified"
        )
        category = html.escape(job["category"])
        location = html.escape(job["location"])
        experience = html.escape(job["experience"])
        employment = html.escape(job["employment"])
        posted = html.escape(job["posted"])

        skills_html = ""

        if job["skills"]:
            skill_chips = "".join(
                f'<span class="skill-chip">{html.escape(skill)}</span>'
                for skill in job["skills"]
            )
            skills_html = (
                '<div class="job-skills">'
                + skill_chips
                + "</div>"
            )

        if job["url"].startswith(("https://", "http://")):
            safe_url = html.escape(job["url"], quote=True)
            apply_html = (
                f'<a class="apply-link" href="{safe_url}" '
                'target="_blank" rel="noopener noreferrer">'
                "↗ View Job / Apply"
                "</a>"
            )
        else:
            apply_html = (
                '<span class="job-detail">'
                "Application link not available"
                "</span>"
            )

        st.markdown(
            f"""
            <div class="job-card">
                <div class="job-topline">
                    <div>
                        <div class="job-tag">{category}</div>
                        <div class="job-title">
                            {index}. {title}
                        </div>
                        <div class="job-company">{company}</div>
                    </div>
                </div>

                <div class="job-details">
                    <div class="job-detail">
                        <span class="job-label">📍 Location</span>
                        {location}
                    </div>

                    <div class="job-detail">
                        <span class="job-label">🎯 Experience</span>
                        {experience}
                    </div>

                    <div class="job-detail">
                        <span class="job-label">💼 Employment Type</span>
                        {employment}
                    </div>

                    <div class="job-detail">
                        <span class="job-label">📅 Posting Date</span>
                        {posted}
                    </div>
                </div>

                {skills_html}

                {apply_html}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 6. HOME SCREEN
# =========================================================

if st.session_state.selected_mode is None:

    st.markdown(
        """
        <div class="welcome">
            <div class="brand-label">✦ AI-POWERED CAREER INTELLIGENCE</div>
            <h1>🧭 SkillMap AI</h1>
            <p>
                Your intelligent career companion.
                Discover in-demand skills, explore opportunities,
                and navigate your career with confidence.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 1.25, 1])

    with center:
        st.markdown("### Where would you like to start?")
        st.markdown(
            '<p class="subtitle">'
            "Choose a workspace to begin your research."
            "</p>",
            unsafe_allow_html=True,
        )

    st.write("")

    feature_left, feature_right = st.columns(2, gap="large")

    with feature_left:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <div class="feature-title">Skill Demand</div>
                <div class="feature-description">
                    Explore industry trends, identify in-demand
                    technologies, and understand which skills
                    employers are looking for.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Explore Skill Demand  →",
            key="home_skill_demand",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.selected_mode = "skill_demand"
            st.rerun()

    with feature_right:
        st.markdown(
            """
            <div class="feature-card">
                <div class="feature-icon">💼</div>
                <div class="feature-title">Job Search</div>
                <div class="feature-description">
                    Discover internships and job openings by role,
                    technology, experience level, and location.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "Find Job Opportunities  →",
            key="home_job_search",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.selected_mode = "job_search"
            st.rerun()

    st.write("")
    st.markdown("---")

    footer_left, footer_center, footer_right = st.columns([1, 2, 1])

    with footer_center:
        st.caption(
            "SkillMap AI · Career research powered by AI and search tools"
        )


# =========================================================
# 7. CHAT WORKSPACE
# =========================================================

else:
    mode = st.session_state.selected_mode

    if mode == "job_search":
        page_title = "💼 Job Search"
        page_description = (
            "Find opportunities that match your preferred role, "
            "skills, experience level, and location."
        )
        input_placeholder = (
            "Example: Find Generative AI internships for freshers in India"
        )
    else:
        page_title = "📊 Skill Demand"
        page_description = (
            "Discover in-demand technologies, industry trends, "
            "and the skills employers value."
        )
        input_placeholder = (
            "Example: What are the most in-demand GenAI skills in India?"
        )

    # Header
    header_left, header_right = st.columns([5, 1])

    with header_left:
        st.title(page_title)
        st.markdown(
            f'<div class="subtitle">{html.escape(page_description)}</div>',
            unsafe_allow_html=True,
        )

    with header_right:
        st.write("")
        if st.button(
            "← Home",
            key="back_home",
            use_container_width=True,
        ):
            st.session_state.selected_mode = None
            st.rerun()

    st.markdown(
        '<hr class="section-divider">',
        unsafe_allow_html=True,
    )

    # Conversation history
    history = st.session_state.messages[mode]

    if not history:
        if mode == "job_search":
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🔎</div>
                    <div class="feature-title">Find your next opportunity</div>
                    <div class="feature-description">
                        Ask for internships, fresher positions,
                        experienced roles, or jobs in a specific location.
                        Your results will appear here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">📈</div>
                    <div class="feature-title">Understand the job market</div>
                    <div class="feature-description">
                        Ask about popular technologies, emerging skills,
                        hiring trends, and the tools employers use.
                        Your research results will appear here.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    for message in history:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])

            elif message.get("is_jobs", False):
                render_job_cards(
                    message["content"],
                    message.get("query", ""),
                )

            else:
                st.markdown(message["content"])

    # Input remains at the bottom of the workspace
    user_query = st.chat_input(input_placeholder)

    if user_query:
        history.append(
            {
                "role": "user",
                "content": user_query,
            }
        )

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner(
                "SkillMap AI is researching and preparing your results..."
            ):
                try:
                    result = run_skillmap_agent(user_query)

                    if not isinstance(result, str):
                        result = str(result)

                    is_jobs = mode == "job_search"

                    if is_jobs:
                        render_job_cards(result, user_query)
                    else:
                        st.markdown(result)

                    history.append(
                        {
                            "role": "assistant",
                            "content": result,
                            "is_jobs": is_jobs,
                            "query": user_query,
                        }
                    )

                except Exception as error:
                    st.error(
                        "Something went wrong while processing your "
                        "request. Check your API configuration and try again."
                    )
                    st.caption(str(error))
