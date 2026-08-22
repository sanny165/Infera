"""
RAG (Retrieval-Augmented Generation) pipeline: retrieves the most relevant
document chunks for a user question via FAISS, then asks Groq to answer
grounded strictly in that retrieved context, with page-level source citations.
"""

from typing import List, TypedDict

from config import RAG_TOP_K
from utils.groq_client import generate
from utils.vector_store import FAISSVectorStore

QA_SYSTEM_PROMPT = (
    "You are a document Q&A assistant. Answer the user's question using ONLY the "
    "provided context excerpts from the document. If the context does not contain "
    "enough information to answer, say so honestly instead of guessing or using "
    "outside knowledge."
)


class RAGAnswer(TypedDict):
    answer: str
    sources: List[int]  # page numbers


def retrieve_relevant_chunks(query: str, vector_store: FAISSVectorStore, k: int = RAG_TOP_K):
    return vector_store.search(query, k=k)


def answer_question(query: str, vector_store: FAISSVectorStore, k: int = RAG_TOP_K) -> RAGAnswer:
    if not vector_store.is_ready():
        return {"answer": "⚠️ No document has been indexed yet.", "sources": []}

    chunks = retrieve_relevant_chunks(query, vector_store, k=k)
    if not chunks:
        return {
            "answer": "⚠️ No sufficiently relevant information was found in the document.",
            "sources": [],
        }

    context_text = "\n\n".join(
        f"[Page {c['page']}] {c['text']}" for c in chunks
    )

    prompt = (
        f"CONTEXT EXCERPTS FROM THE DOCUMENT:\n{context_text}\n\n"
        f"QUESTION: {query}\n\n"
        "Answer the question grounded strictly in the context above. "
        "Be concise and direct."
    )

    answer_text = generate(prompt, system=QA_SYSTEM_PROMPT, temperature=0.2, max_tokens=800)

    # De-duplicate page numbers while preserving order of relevance
    seen = set()
    sources = []
    for c in chunks:
        if c["page"] not in seen:
            seen.add(c["page"])
            sources.append(c["page"])

    return {"answer": answer_text, "sources": sources}
