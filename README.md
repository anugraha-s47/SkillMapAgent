# SkillMap Agent 🤖

An AI-powered career exploration agent that helps users explore in-demand skills and discover relevant job opportunities using Generative AI, web search, and job-search APIs.

## 📌 Overview

SkillMap Agent combines a Large Language Model (LLM) with external tools to help users understand current skill trends and search for job opportunities.

Instead of relying only on the model's existing knowledge, the agent can use external search tools to retrieve relevant information and job listings. It also supports conversational follow-up questions to make career exploration more interactive.

## ✨ Features

- **AI-Powered Career Assistance:** Ask questions about technologies, career paths, and skills to learn.
- **Skill Demand Research:** Uses Tavily Search to explore information about trending and in-demand skills.
- **Job Discovery:** Uses the JSearch API to find relevant job listings based on skill and location.
- **Job Categorization:** Organizes job results into categories such as internships, fresher or entry-level roles, and experienced positions where listing information allows.
- **Conversational Follow-Ups:** Ask follow-up questions about previously retrieved job listings.
- **Tool-Calling Agent:** Uses LangChain and LangGraph to connect the language model with external tools.
- **Conversation Checkpointing:** Uses in-memory checkpointing to retain conversation context during the running session.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| LangChain | LLM integration and tool orchestration |
| LangGraph | Agent execution and conversation checkpointing |
| Groq | Language model inference |
| Tavily Search | Web research for skill-demand queries |
| JSearch API | Job listing retrieval |
| python-dotenv | Loading API keys from environment variables |
| Streamlit | Web interface, if using `app.py` |

## 🏗️ How It Works

1. **User Input:** The user asks about skill demand or job opportunities.
2. **Agent Decision:** The LLM interprets the request and determines whether an available tool is needed.
3. **Skill Research:** For skill-demand questions, the agent can use Tavily Search to retrieve relevant web information.
4. **Job Search:** For job-related questions, the agent can use JSearch to retrieve listings matching the requested skill and location.
5. **Result Processing:** Job listings are processed and categorized using available listing details.
6. **Response Generation:** The LLM generates a conversational response based on the retrieved information.
7. **Follow-Up Questions:** The user can ask additional questions about the results within the supported conversation context.

## ⚙️ Prerequisites

Before running the project, ensure you have:

- Python installed
- Git installed
- A Groq API key
- A Tavily API key
- A RapidAPI key with access to the JSearch API

The availability and usage limits of external APIs depend on your account and plan.

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/SkillMapAgent.git
cd SkillMapAgent
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the Python packages used by the project:

```bash
python -m pip install langchain langchain-groq langchain-tavily langgraph requests python-dotenv streamlit
```

If the project uses additional packages, install those as well.

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
RAPIDAPI_KEY=your_rapidapi_key
```

Use the exact variable names expected by your Python code. If your JSearch implementation uses a different variable name, update this example accordingly.

**Security:** Never commit your real `.env` file or publish API keys on GitHub.

### 5. Run the agent

To run the terminal-based agent:

```bash
python main.py
```

If `app.py` contains the Streamlit interface, launch it with:

```bash
python -m streamlit run app.py
```

Use the interface or terminal prompt to ask questions about skill trends and job opportunities.

## 💬 Example Queries

Try asking:

- `What skills are trending in Generative AI?`
- `Show me GenAI internships in India`
- `Show me React developer internships in Coimbatore`
- `Find Python developer jobs in Chennai`
- `Tell me about Job 2`

The actual results depend on the search APIs, their available data, and your configured API limits.

## 🔐 Environment Variables

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates requests to Groq |
| `TAVILY_API_KEY` | Authenticates Tavily web searches |
| `RAPIDAPI_KEY` | Authenticates requests to the JSearch API |

Keep API credentials private and use environment variables instead of hardcoding secrets in source files.

## ⚠️ Limitations

- Job listings and skill-demand information depend on external search services and their available data.
- Job categorization is based on the information returned by job listings and may not always be accurate.
- Free API plans may impose request or token limits.
- In-memory conversation checkpointing does not provide permanent conversation storage; session context may be lost when the application restarts.
- Job availability and application links should be verified on the original job provider's website.

## 🔮 Future Enhancements

- Add personalized skill-gap analysis based on a user's current skills and target role.
- Generate structured learning roadmaps for selected career paths.
- Add job filtering by experience, work mode, company, and location.
- Save user preferences and job bookmarks.
- Improve token efficiency and conversation-history management.
- Add a polished career dashboard with saved searches and skill trends.

## 👩‍💻 Author

**S. Anugraha**

Computer Science Engineering Student | Aspiring Software Developer | Generative AI Enthusiast

## 📄 License

Choose and add an appropriate open-source license if you intend to allow others to reuse, modify, or distribute this project.
