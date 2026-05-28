"""Ingestion pipeline for the RAG application.

Ties together the loader, chunker, embedder and vector store to build the
document index from the configured source directory.
"""

from . import config
from .loader import load_documents
from .chunker import split_text
from .embedder import Embedder
from .vectorstore import VectorStore


def ingest() -> None:
    """Run the full ingestion pipeline.

    Loads every supported document from ``config.DOCS_DIR``, splits each one
    into overlapping chunks, embeds the chunks in a single batch, and persists
    them in the Chroma vector store.
    """
    # ------------------------------------------------------------------
    # 1. Load documents
    # ------------------------------------------------------------------
    print(f"Loading documents from '{config.DOCS_DIR}' ...")
    if not config.DOCS_DIR.exists():
        print(f"Directory '{config.DOCS_DIR}' does not exist. Nothing to ingest.")
        return

    documents = load_documents(config.DOCS_DIR)
    if not documents:
        print("No supported documents found.")
        return

    print(f"Loaded {len(documents)} document(s).")

    # ------------------------------------------------------------------
    # 2. Chunk documents
    # ------------------------------------------------------------------
    print(
        f"Chunking with size={config.CHUNK_SIZE}, overlap={config.CHUNK_OVERLAP} ..."
    )

    all_ids: list[str] = []
    all_texts: list[str] = []
    all_metadatas: list[dict] = []

    for doc in documents:
        source = doc["source"]
        text = doc["text"]
        chunks = split_text(text, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        print(f"  {source} -> {len(chunks)} chunk(s)")

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{source}::{idx}"
            all_ids.append(chunk_id)
            all_texts.append(chunk)
            all_metadatas.append({"source": source, "chunk_index": idx})

    if not all_texts:
        print("No text chunks produced. Nothing to store.")
        return

    print(f"Total chunks to embed: {len(all_texts)}")

    # ------------------------------------------------------------------
    # 3. Embed chunks (single batch)
    # ------------------------------------------------------------------
    print(f"Embedding {len(all_texts)} chunk(s) using '{config.EMBED_MODEL}' ...")
    embedder = Embedder(config.EMBED_MODEL)
    embeddings = embedder.embed(all_texts)
    print("Embedding complete.")

    # ------------------------------------------------------------------
    # 4. Store in vector database
    # ------------------------------------------------------------------
    print(f"Storing chunks in vector database at '{config.CHROMA_DIR}' ...")
    store = VectorStore(str(config.CHROMA_DIR))
    store.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_texts,
        metadatas=all_metadatas,
    )
    print(f"Ingestion finished. {store.count()} chunk(s) in the index.")


if __name__ == "__main__":
    ingest()
