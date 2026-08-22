"""
FAISS-backed semantic vector store for a single uploaded document.

Uses an inner-product index over L2-normalized vectors, which is
mathematically equivalent to cosine similarity search.
"""

from typing import List, Optional, TypedDict

import faiss

from utils.embeddings import embed_query, embed_texts


class ScoredChunk(TypedDict):
    chunk_id: int
    page: int
    text: str
    score: float


class FAISSVectorStore:
    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.chunks: List[dict] = []

    def build(self, chunks: List[dict]) -> None:
        """chunks: list of {"chunk_id", "page", "text"}"""
        if not chunks:
            raise ValueError("Cannot build a vector store from zero chunks.")
        self.chunks = chunks
        texts = [c["text"] for c in chunks]
        embeddings = embed_texts(texts)
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

    def is_ready(self) -> bool:
        return self.index is not None and self.index.ntotal > 0

    def search(self, query: str, k: int = 5) -> List[ScoredChunk]:
        if not self.is_ready():
            return []
        query_vec = embed_query(query)
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(query_vec, k)
        results: List[ScoredChunk] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append(
                {
                    "chunk_id": chunk["chunk_id"],
                    "page": chunk["page"],
                    "text": chunk["text"],
                    "score": float(score),
                }
            )
        return results
