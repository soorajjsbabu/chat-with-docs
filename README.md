# 📄 Chat With Your Documents

A full-stack RAG (Retrieval-Augmented Generation) app that lets you upload your own documents and ask natural language questions about them. Answers are grounded in your document content with source citations — the model won't guess if the answer isn't there.

Built with Python, SentenceTransformers, ChromaDB, Ollama, FastAPI, and Vue.js. Everything runs locally — no OpenAI API key, no cloud costs.

![Chat With Your Docs UI](./screenshots/Screenshot%202026-05-29%20152958.png)

---

## 💡 How It Works

RAG = **Retrieval-Augmented Generation**. Instead of asking an LLM a question blind, the app first retrieves the most relevant passages from your uploaded documents, then feeds those passages to the LLM as context. The model answers from *your data* — and says "I don't know" if the answer isn't there.

The pipeline runs in six stages:

```
1. LOAD      → parse uploaded PDF / TXT / MD files from memory
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
| Language       | Python 3.12                                 |

---

## ✅ Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Git**
- **Ollama** — download from [ollama.com](https://ollama.com)
- An NVIDIA GPU is recommended (RTX 3060 or better) but not required

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/chat-with-docs.git
cd chat-with-docs
```

### 2. Create and activate a virtual environment

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up Ollama

Pull the model (~5 GB download):

```bash
ollama pull llama3.1:8b
```

### 5. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Running the App

You need **three terminals** running simultaneously:

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — FastAPI backend:**
```bash
# From project root, with venv activated
uvicorn api.main:app --reload
```
Backend runs at **http://localhost:8000**

**Terminal 3 — Vue frontend:**
```bash
cd frontend
npm run dev
```
Frontend runs at **http://localhost:5173**

---

## 📖 How to Use

1. Open **http://localhost:5173** in your browser
2. Click **Choose Files** and select one or more PDF, TXT, or MD files
3. Click **Upload** and wait for the confirmation message (e.g. *"Processed 1 file(s). 42 chunks added"*)
4. Type a question about your documents in the chat input and press **Enter** or click **Send**
5. The assistant will answer with source citations below each response

> **Note:** The vector store clears every time the backend restarts. Re-upload your files after restarting the server.

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
│   └── package.json
├── tests/
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint      | Description                              |
|--------|---------------|------------------------------------------|
| POST   | `/api/query`  | Ask a question — `{"question": "string"}` |
| POST   | `/api/upload` | Upload files for indexing (`multipart/form-data`) |
| GET    | `/api/health` | Health check — returns `{"status": "ok"}` |

Interactive API docs available at **http://localhost:8000/docs**

---

## ⚙️ Configuration

All settings are in `src/config.py`:

```python
EMBED_MODEL   = "all-MiniLM-L6-v2"   # SentenceTransformers model
LLM_MODEL     = "llama3.1:8b"         # Ollama model name
CHUNK_SIZE    = 800                    # Characters per chunk
CHUNK_OVERLAP = 150                    # Overlap between chunks
TOP_K         = 4                      # Chunks retrieved per question
```

Swap `LLM_MODEL` to any model supported by Ollama (e.g. `mistral:7b`, `llama3.2:3b`).

---

## 🗺️ Roadmap

- [x] Project setup and environment configuration
- [x] Document loader — PDF, TXT, MD support
- [x] Text chunker with configurable overlap
- [x] SentenceTransformers embedder with GPU support
- [x] ChromaDB vector store with persistence
- [x] RAG query engine with source citations
- [x] "I don't know" guardrail — model abstains when answer isn't in context
- [x] FastAPI backend with query and upload endpoints
- [x] Vue 3 frontend with dark theme chat UI
- [x] Live file upload — documents indexed at runtime, no static folder needed
- [x] Multi-file upload support
- [ ] Answer faithfulness evaluation script
- [ ] Streaming responses (token-by-token)
- [ ] Docker + docker-compose for one-command setup

---

## 🧠 What I Learned

- How RAG works end-to-end — from chunking strategy to prompt design
- Why embedding normalisation matters for cosine similarity search
- How vector databases differ from traditional databases
- Designing a "responsible AI" guardrail that prevents hallucination
- Connecting a FastAPI backend to a Vue 3 frontend with CORS
- Handling multipart file uploads in FastAPI with `python-multipart`

---

## 📝 Known Limitations

- Vector store clears on server restart (persistence across sessions is a planned improvement)
- Large PDFs with complex layouts (columns, tables) may have lower retrieval accuracy due to pypdf text extraction order
- No authentication — intended for local use only

---

## 👤 Author

**Sooraj Srinivasa Babu**  
[LinkedIn](https://linkedin.com/in/soorajsrinivasababu) · [GitHub](https://github.com/soorajjsbabu)
