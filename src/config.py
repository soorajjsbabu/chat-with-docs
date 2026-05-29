from pathlib import Path

DOCS_DIR = Path("docs")                # Directory containing the source documents to be ingested and indexed
CHROMA_DIR = Path(".chroma")           # Directory where the Chroma vector database files will be persisted
EMBED_MODEL = "all-MiniLM-L6-v2"       # Name of the sentence-transformers model used to generate text embeddings
LLM_MODEL = "llama3.1:8b"              # Name of the Ollama LLM model used for generating responses
OLLAMA_URL = "http://localhost:11434"  # Base URL for the local Ollama API server
CHUNK_SIZE = 1200                      # Maximum number of characters per document chunk for embedding
CHUNK_OVERLAP = 200                    # Number of characters to overlap between consecutive chunks for context continuity
TOP_K = 6                              # Number of top similar chunks to retrieve from the vector store for each query
