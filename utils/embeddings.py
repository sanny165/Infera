"""
Embedding generation using Sentence Transformers.

The model is cached as a Streamlit resource so it's loaded once per session
(not re-downloaded / re-loaded on every rerun).
"""

from typing import List

import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL_NAME


@st.cache_resource(show_spinner=False)
def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of strings into a (n, dim) float32 numpy array, L2-normalized
    (so inner product search == cosine similarity in the FAISS index)."""
    model = load_embedding_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.astype("float32")


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])
