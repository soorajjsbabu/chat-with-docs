"""Vector store for the RAG application.

Wraps ChromaDB to persist and search dense text embeddings.
A vector database is fundamentally different from a regular database:

- Regular databases (SQL, key-value, document stores) answer questions like
  "Find the row where id = 42" or "Find all invoices > $100". They use
  exact matching, indexes on discrete fields, or full-text search on keywords.

- Vector databases answer "Find the chunks most similar in meaning to this
  text." They store high-dimensional floating-point vectors and use
  approximate-nearest-neighbor (ANN) algorithms to search by *semantic
  similarity* rather than exact values. This is essential for RAG because
  a user's question rarely contains the exact same words as the answer in
  the document, but their embeddings will be close in vector space.
"""

from typing import List, Dict, Any

import chromadb


class VectorStore:
    """Manages persistent storage and semantic retrieval of text embeddings."""

    def __init__(self, persist_dir: str):
        """Initialize the vector store.

        Args:
            persist_dir: Directory on disk where Chroma will save the
                         database files so data survives between runs.
        """
        # Create a persistent Chroma client that writes data to disk.
        self._client = chromadb.PersistentClient(path=persist_dir)
        # Get or create a default collection to hold our document chunks.
        self._collection = self._client.get_or_create_collection(name="documents")

    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Store chunks and their embeddings in the vector database.

        Args:
            ids: Unique identifiers for each chunk (e.g., "doc_0_chunk_1").
            embeddings: Dense embedding vectors, one per chunk.
            documents: The raw text content of each chunk.
            metadatas: Optional dicts of metadata per chunk (e.g., source filename).
        """
        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self, query_embedding: List[float], top_k: int
    ) -> Dict[str, Any]:
        """Find the most semantically similar chunks to a query.

        Args:
            query_embedding: The embedding vector of the user's question.
            top_k: Maximum number of closest chunks to return.

        Returns:
            A dictionary with Chroma query results, including:
            - 'ids': matched chunk ids
            - 'distances': similarity scores
            - 'documents': the matched text chunks
            - 'metadatas': metadata for each match
        """
        return self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

    def count(self) -> int:
        """Return the total number of chunks stored in the collection."""
        return self._collection.count()

    def clear(self) -> None:
        """Delete every chunk by removing and recreating the collection."""
        self._client.delete_collection("documents")
        self._collection = self._client.get_or_create_collection(name="documents")
