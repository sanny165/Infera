"""
Thin wrapper around the Groq Python SDK so the rest of the app never
touches API keys or raw client construction directly.
"""

import streamlit as st
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL


class GroqNotConfiguredError(Exception):
    pass


class GroqGenerationError(Exception):
    pass


@st.cache_resource(show_spinner=False)
def get_client() -> Groq:
    if not GROQ_API_KEY:
        raise GroqNotConfiguredError(
            "GROQ_API_KEY is not set. Add it to your .env file locally, or to "
            "your Streamlit Community Cloud app's Secrets after deployment."
        )
    return Groq(api_key=GROQ_API_KEY)


def generate(prompt: str, system: str = "", temperature: float = 0.3, max_tokens: int = 2000) -> str:
    """Single-turn text generation against the configured Groq model."""
    client = get_client()
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()
    except GroqNotConfiguredError:
        raise
    except Exception as e:
        raise GroqGenerationError(f"❌ Unable to generate analysis. Please try again. ({e})") from e
