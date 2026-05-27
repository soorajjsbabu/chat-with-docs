"""Embedder for the RAG application.

Wraps sentence-transformers to encode text chunks into dense vector
embeddings. Embeddings are L2-normalized so that similarity search
with cosine or dot-product is fast, fair, and magnitude-invariant.
"""

from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    """Encodes text into normalized embedding vectors.

    Args:
        model_name: The sentence-transformers model identifier to load.
    """

    def __init__(self, model_name: str):
        # Load the pretrained sentence-transformers model.
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Encode a list of strings into normalized embeddings.

        Args:
            texts: The strings to encode.

        Returns:
            A list of L2-normalized embedding vectors (each a list of floats).
        """
        # Compute dense embeddings. The model returns a NumPy array
        # of shape (num_texts, embedding_dimension).
        embeddings: np.ndarray = self._model.encode(texts)

        # L2-normalize each vector so its magnitude becomes 1.
        # Why normalize?
        #
        # 1. Cosine similarity = dot product of unit vectors.
        #    After normalization, a simple dot product gives the same ranking
        #    as full cosine similarity, which is faster to compute.
        #
        # 2. Magnitude invariance.
        #    Longer texts can produce vectors with larger magnitudes.
        #    Normalization removes that bias so every chunk is judged purely
        #    on angle/direction, not on how long the original text was.
        #
        # 3. Fair comparison across queries.
        #    A short query and a long document chunk naturally have different
        #    magnitudes; normalization puts them on equal footing.
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        # Avoid division by zero for empty strings.
        normalized = np.divide(embeddings, norms, out=np.zeros_like(embeddings), where=norms != 0)

        # Convert back to plain Python lists for easy serialization.
        return normalized.tolist()
