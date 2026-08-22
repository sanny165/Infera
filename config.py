"""
Central configuration for Document-Summarizer.

Reads settings from (in priority order):
  1. Streamlit secrets (st.secrets)   -> used on Streamlit Community Cloud
  2. Environment variables (.env)     -> used for local development

This means the SAME code works locally and after deployment without changes.
"""

import os

import streamlit as st
from dotenv import load_dotenv

# Load variables from a local .env file if present (no-op on Streamlit Cloud)
load_dotenv()


def get_setting(key: str, default: str = "") -> str:
    """Fetch a setting from st.secrets first, then environment variables."""
    try:
        # st.secrets raises if no secrets.toml exists at all, so guard it
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.environ.get(key, default)


# ---------------------------------------------------------------------------
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>> ADD YOUR KEYS HERE <<<<<<<<<<<<<<<<<<<<<<<<<<<
# Locally: put these in a `.env` file (see .env.example).
# On Streamlit Community Cloud: put these in the app's "Secrets" settings
#   under Settings -> Secrets, using the same TOML format as .env.example.
# ---------------------------------------------------------------------------
GROQ_API_KEY: str = get_setting("GROQ_API_KEY", "")

# Groq model used for summaries / key points / main ideas / suggestions / RAG Q&A.
# NOTE: llama-3.1-8b-instant and llama-3.3-70b-versatile were deprecated by Groq
# in June 2026. openai/gpt-oss-120b is the current recommended general-purpose
# model. Override via GROQ_MODEL if Groq's lineup changes again.
GROQ_MODEL: str = get_setting("GROQ_MODEL", "openai/gpt-oss-120b")

# Sentence-Transformers embedding model (lightweight, good for semantic search)
EMBEDDING_MODEL_NAME: str = get_setting(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)

# ---------------------------------------------------------------------------
# Pipeline tuning knobs (safe to leave as-is)
# ---------------------------------------------------------------------------
CHUNK_SIZE = int(get_setting("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(get_setting("CHUNK_OVERLAP", "150"))
RAG_TOP_K = int(get_setting("RAG_TOP_K", "5"))

# Threshold: average characters/page below this triggers OCR fallback for PDFs
MIN_CHARS_PER_PAGE_FOR_TEXT_PDF = 20

# Map-reduce summarization kicks in above this many characters of source text
LARGE_DOC_CHAR_THRESHOLD = 12000
MAP_CHUNK_CHAR_SIZE = 6000

SUPPORTED_EXTENSIONS = ["pdf", "png", "jpg", "jpeg"]
MAX_FILE_SIZE_MB = 25
