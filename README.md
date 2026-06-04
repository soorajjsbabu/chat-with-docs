# 📄 Chat With Your Documents

A full-stack RAG (Retrieval-Augmented Generation) app that lets you upload your own documents and ask natural language questions about them. Answers are grounded in your document content with source citations — the model won't guess if the answer isn't there.

Built with Python, SentenceTransformers, ChromaDB, Ollama, FastAPI, and Vue.js. Runs fully locally — no OpenAI API key, no cloud costs. One-command setup with Docker.

![Chat With Your Docs UI](./screenshots/UI.png)

---

## 💡 How It Works

RAG = **Retrieval-Augmented Generation**. Instead of asking an LLM a question blind, the app first retrieves the most relevant passages from your uploaded documents, then feeds those passages to the LLM as context. The model answers from *your data* — and says "I don't know" if the answer isn't there.

The pipeline runs in six stages:

```
1. LOAD      → parse uploaded PDF / TXT / DOCX/MD files from memory
2. CHUNK     → split documents into overlapping passages
3. EMBED     → convert each chunk into a vector (SentenceTransformers)
4. STORE     → persist vectors in a local vector database (ChromaDB)
5. RETRIEVE  → embed the user's question, find the top-k nearest chunks
6. GENERATE  → pass those chunks to an LLM (Ollama) and return answer + sources
```

Every time the backend starts, the vector store is cleared — only files you upload through the UI are ever indexed.

---

## 🛠️ Tech Stack

| Layer          | Tool                                        |
|----------------|---------------------------------------------|
| LLM            | [Ollama](https://ollama.com) + Llama 3.1 8B |
| Embeddings     | SentenceTransformers (`all-MiniLM-L6-v2`)   |
| Vector DB      | ChromaDB (local, persistent)                |
| PDF Parsing    | pypdf                                       |
| Backend API    | FastAPI + Uvicorn                           |
| Frontend       | Vue 3 + Vite (Composition API)              |
| Containerisation | Docker + Docker Compose                   |
| Language       | Python 3.12                                 |

---

## ✅ Prerequisites

**To run with Docker (recommended):**
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- NVIDIA GPU with drivers 526+ (optional, for GPU acceleration)

**To run locally without Docker:**
- Python 3.10+
- Node.js 22+
- Git
- [Ollama](https://ollama.com)

---

## 🐳 Quick Start with Docker (Recommended)

This is the easiest way to run the app — one command starts everything.

### 1. Clone the repository

```bash
git clone https://github.com/soorajjsbabu/chat-with-docs.git
cd chat-with-docs
```

### 2. Start all services

```bash
docker compose up --build
```

This starts three containers automatically:
- **Ollama** — LLM server (port 11434)
- **FastAPI backend** — REST API (port 8000)
- **Vue frontend** — served by Nginx (port 5173)

First build takes 3-5 minutes while it downloads images and installs dependencies.

### 3. Pull the LLM model

In a new terminal (while docker compose is running):

```bash
docker exec -it chat-with-docs-ollama-1 ollama pull llama3.1:8b
```

This downloads the Llama 3.1 8B model (~5 GB) into the container.

### 4. Open the app

Go to **http://localhost:5173** in your browser.

> **GPU Note:** If you have an NVIDIA GPU (driver 526+), Ollama automatically uses it inside Docker for much faster responses. No extra configuration needed.

---

## 🚀 Running Without Docker

If you prefer to run without Docker, you need three terminals.

### Setup

```bash
# 1. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Pull the Ollama model
ollama pull llama3.1:8b

# 4. Install frontend dependencies
cd frontend && npm install && cd ..
```

### Run

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — FastAPI backend:**
```bash
uvicorn api.main:app --reload
```

**Terminal 3 — Vue frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**

---

## 📖 How to Use

1. Open **http://localhost:5173**
2. Click **Choose Files** and select a PDF, TXT, DOCX or MD file
3. Click **Upload** and wait for the confirmation (e.g. *"Processed 1 file(s). 42 chunks added"*)
4. Repeat steps 2–3 to upload additional documents one at a time
5. Type a question about your documents and press **Enter** or click **Send**
6. The assistant answers with source citations below each response

> **Note:** The vector store clears on every backend restart. Re-upload your files after restarting.

---

## 📁 Project Structure

```
chat-with-docs/
├── src/
│   ├── config.py         # All settings — models, chunk size, top-k
│   ├── loader.py         # Stage 1: parse PDFs and text files from memory
│   ├── chunker.py        # Stage 2: split text into overlapping chunks
│   ├── embedder.py       # Stage 3: convert chunks to vectors
│   ├── vectorstore.py    # Stage 4: store and query vectors (ChromaDB)
│   ├── ingest.py         # Orchestrates stages 1–4
│   └── rag.py            # Stages 5–6: retrieve chunks + generate answer
├── api/
│   └── main.py           # FastAPI app — /api/query and /api/upload endpoints
├── frontend/
│   ├── src/
│   │   ├── App.vue       # Main chat UI component
│   │   └── style.css     # Global styles
│   ├── Dockerfile        # Frontend container (Node 22 + Nginx)
│   └── package.json
├── screenshots/
│   └── ui.png
├── tests/
├── Dockerfile            # Backend container (Python 3.12)
├── docker-compose.yml    # Orchestrates all 3 services
├── .dockerignore
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint             | Description                                       |
|--------|----------------------|---------------------------------------------------|
| POST   | `/api/query`         | Ask a question — `{"question": "string"}`         |
| POST   | `/api/query/stream`  | Stream answer token-by-token (text/event-stream)  |
| POST   | `/api/upload`        | Upload files (`multipart/form-data`)              |
| GET    | `/api/health`        | Health check — `{"status": "ok"}`                 |

Interactive API docs: **http://localhost:8000/docs**

---

## ⚙️ Configuration

All settings are in `src/config.py`:

```python
EMBED_MODEL   = "all-MiniLM-L6-v2"      # SentenceTransformers model
LLM_MODEL     = "llama3.1:8b"           # Ollama model name
CHUNK_SIZE    = 1200                    # Characters per chunk
CHUNK_OVERLAP = 200                     # Overlap between chunks
TOP_K         = 6                       # Chunks retrieved per question
OLLAMA_URL    = os.getenv("OLLAMA_URL", "http://localhost:11434")
```

Swap `LLM_MODEL` to any model supported by Ollama (e.g. `mistral:7b`, `llama3.2:3b`).

---

## 🗺️ Roadmap

- [x] Project setup and environment configuration
- [x] Document loader — PDF, TXT, MD, DOCX support
- [x] Text chunker with configurable overlap
- [x] SentenceTransformers embedder with GPU support
- [x] ChromaDB vector store with persistence
- [x] RAG query engine with source citations
- [x] "I don't know" guardrail — model abstains when answer isn't in context
- [x] FastAPI backend with query and upload endpoints
- [x] Vue 3 frontend with dark theme chat UI
- [x] Live file upload — documents indexed at runtime
- [x] Multi-file upload support
- [x] Docker + Docker Compose — one-command setup
- [x] NVIDIA GPU passthrough for Ollama in Docker
- [x] Answer faithfulness evaluation script
- [x] Streaming responses (token-by-token)
- [x] Uploaded files panel showing filenames with thumbnails
- [x] Multiple file upload (up to 5 files simultaneously)

---

## 🧠 What I Learned

- How RAG works end-to-end — from chunking strategy to prompt design
- Why embedding normalisation matters for cosine similarity search
- How vector databases differ from traditional databases
- Designing a responsible AI guardrail that prevents hallucination
- Connecting a FastAPI backend to a Vue 3 frontend with CORS
- Handling multipart file uploads in FastAPI with `python-multipart`
- Multi-container Docker setup with service networking and named volumes
- GPU passthrough to Docker containers using NVIDIA Container Toolkit
- Building a RAG evaluation framework to measure retrieval accuracy, answer faithfulness and abstention rate across multiple documents
- Implementing token-by-token streaming with server-sent events connecting FastAPI StreamingResponse to Vue's ReadableStream API

---

## 📝 Known Limitations

- Vector store clears on server restart (persistence across sessions is a planned improvement)
- Large PDFs with complex layouts may have lower retrieval accuracy due to pypdf text extraction
- No authentication — intended for local use only

---

## 👤 Author

**Sooraj Srinivasa Babu**  
[LinkedIn](https://linkedin.com/in/soorajsrinivasababu) · [GitHub](https://github.com/soorajjsbabu)
