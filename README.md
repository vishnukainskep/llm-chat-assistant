# Gen-AI: ReAct Agent with RAG & Stateful Memory

A powerful AI assistant platform featuring a **ReAct (Reason + Act)** agent, **Retrieval-Augmented Generation (RAG)** for API documentation, and **session-specific persistent memory**.

## 🚀 Features

- **ReAct Agent**: An intelligent agent that reasons through tasks and chooses the right tools to execute.
- **RAG for API Documentation**: Automatically retrieves API details (Methods, Endpoints, Base URLs) from `docs.txt` using ChromaDB and Azure OpenAI Embeddings.
- **Stateful Persistence**: Session-specific chat history stored in **MongoDB**, allowing context retention across different user sessions.
- **Comprehensive Toolset**:
    - `rag_search`: Searches documentation for API specs.
    - `api_agent`: Executes REST API calls (GET, POST, etc.) dynamically.
    - `python_expert`: Executes and debugs Python code.
    - `current_time`, `solve_math`, `joke_generator`: Utility tools for common tasks.
- **Modern UI**: A responsive and clean chat interface built with React, TypeScript, and Tailwind CSS.

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Frontend**: React (TypeScript) + Vite
- **AI Orchestration**: LangChain
- **LLM**: Azure OpenAI (GPT-4)
- **Vector Database**: ChromaDB (for RAG)
- **Database**: MongoDB (for Chat History)

## 🛠️ Getting Started

### Prerequisites

- Python 3.9+
- Node.js & npm
- Azure OpenAI Account
- MongoDB Instance (Atlas or Local)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file based on `.env.template` and fill in your credentials:
   ```env
   AZURE_OPENAI_API_KEY=...
   AZURE_OPENAI_ENDPOINT=...
   AZURE_OPENAI_MODEL=gpt-4
   CONNECTIONSTRING=mongodb+srv://...
   EMBEDDING_ENDPOINT=...
   EMBEDDING_DEPLOYMENT=...
   ```
5. Run the backend:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## 📝 Usage Examples

### Searching & Calling APIs
**User**: "show all posts pls"
1. **Agent Thought**: I need to find the API endpoint for posts.
2. **Action**: `rag_search` -> Returns details for `https://jsonplaceholder.typicode.com/posts`.
3. **Action**: `api_agent` -> Calls the GET method on the URL.
4. **Final Answer**: Displays the list of posts retrieved from the API.

### Session Isolation
The system uses `session_id` to keep conversations separate. Alex and Bob can chat with the same agent without their histories mixing.

## 📂 Project Structure

```text
GEN-AI/
├── backend/
│   ├── app/
│   │   ├── agents/      # ReAct Agent logic
│   │   ├── tools/       # Custom tool implementations
│   │   ├── vector/      # RAG & ChromaDB logic
│   │   ├── routes/      # FastAPI endpoints
│   │   └── db/          # Database connections
│   ├── main.py          # Backend entry point
│   └── requirements.txt
├── frontend/
│   ├── src/             # React components & logic
│   └── package.json
└── README.md            # You are here
```


