from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.loader import load_document_from_bytes
from src.rag import RAG


class QueryRequest(BaseModel):
    question: str


class QueryResponse(BaseModel):
    answer: str
    sources: List[str]


class HealthResponse(BaseModel):
    status: str


class UploadResponse(BaseModel):
    message: str
    files: List[str]
    chunks_added: int


# Global RAG instance populated on startup.
rag: RAG


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag
    rag = RAG()
    rag.clear_index()  # Start fresh; only uploaded files will be used
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    result = rag.answer(request.question)
    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload(files: List[UploadFile] = File(...)) -> UploadResponse:
    documents = []
    processed = []

    for uploaded_file in files:
        content = await uploaded_file.read()
        doc = load_document_from_bytes(content, uploaded_file.filename)
        if doc:
            documents.append(doc)
            processed.append(uploaded_file.filename)

    chunks_added = 0
    if documents:
        chunks_added = rag.ingest_documents(documents)

    return UploadResponse(
        message=f"Processed {len(processed)} file(s).",
        files=processed,
        chunks_added=chunks_added,
    )


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
