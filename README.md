# 📄 Document-Summarizer

**AI-Powered Document Summary Assistant** — upload a PDF or image (including
scanned documents), and get a content-proportional summary, key points, main
ideas, improvement suggestions, and a document-grounded Q&A chat, all backed
by a real RAG pipeline.

---

## 1. Problem Statement

Reading and digesting long documents — research papers, reports, scanned
forms — takes time. This app automates that: it extracts a document's content
(even from scans, via OCR), indexes it semantically, and uses an LLM to
produce grounded summaries, extracted key information, and answers to
follow-up questions — without hallucinating content that isn't in the source.

## 2. Features

- 📤 Upload PDF, PNG, JPG, JPEG (drag-and-drop or file picker)
- 🔎 Dual-path text extraction: direct PDF text layer **or** Tesseract OCR
  fallback for scanned PDFs and images
- ✂️ Text cleaning, normalization, and page-aware chunking
- 🧠 Semantic embeddings (Sentence-Transformers) indexed in **FAISS**
- 📝 Content-proportional summaries (Short / Medium / Long) with
  map-reduce handling for large documents
- 🔑 Key Points (bullet list) and 🎯 Main Ideas (topic headings for recall)
- 💡 Improvement suggestions (organization, clarity, completeness, consistency)
- 💬 RAG-based Q&A grounded in the document, with page-number source citations
- ⬇️ Downloadable summary
- Clean error handling and visible pipeline loading states

## 3. Architecture

```
Document (PDF/Image)
        │
        ▼
 Extract / OCR   (PyMuPDF text layer, or Tesseract OCR fallback)
        │
        ▼
 Clean & Chunk    (page-aware chunking, LangChain text splitter)
        │
        ▼
 Embed            (Sentence-Transformers all-MiniLM-L6-v2)
        │
        ▼
 FAISS Vector Store
        │
   ┌────┴─────┐
   ▼          ▼
Summary /   RAG Retrieval (question → top-k relevant chunks)
Key Points /      │
Main Ideas /      ▼
Suggestions    Groq LLM → Grounded Answer + Page Sources
   │
   ▼
Streamlit UI
```

## 4. Tech Stack

| Layer            | Technology                              |
|-------------------|------------------------------------------|
| Frontend/UI       | Streamlit                                |
| PDF Parsing       | PyMuPDF (fitz)                           |
| OCR               | Tesseract + pytesseract                  |
| Text Chunking     | LangChain Text Splitters                 |
| Embeddings        | Sentence-Transformers (all-MiniLM-L6-v2) |
| Vector Database   | FAISS                                    |
| LLM               | Groq API                                 |
| Deployment        | Streamlit Community Cloud                |

## 5. RAG Workflow

**Indexing:** Document → Extract Text → Chunk Text → Generate Embeddings → FAISS
**Retrieval:** Question → Query Embedding → FAISS Similarity Search → Top-K
Relevant Chunks → Context → (Context + Question) → Groq → Grounded Response

## 6. Project Structure

```
Document-Summarizer/
├── app.py
├── config.py
├── utils/
│   ├── pdf_extractor.py
│   ├── ocr.py
│   ├── text_processor.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── rag.py
│   ├── summarizer.py
│   └── groq_client.py
├── prompts/
│   ├── summary_prompt.txt
│   ├── key_points_prompt.txt
│   ├── main_ideas_prompt.txt
│   └── improvement_prompt.txt
├── sample_documents/
├── assets/screenshots/
├── requirements.txt
├── packages.txt
├── .env.example
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── .gitignore
├── LICENSE
└── README.md
```

## 7. Installation (Local)

**Prerequisites:** Python 3.10+, and the Tesseract OCR engine installed at the
system level (pytesseract calls the local `tesseract` binary).

Install Tesseract:
- **macOS:** `brew install tesseract`
- **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr`
- **Windows:** install from https://github.com/UB-Mannheim/tesseract/wiki and
  ensure it's on your PATH

Clone and set up the project:

```bash
git clone <your-repo-url>
cd Document-Summarizer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 8. Environment Setup

> ⚠️ **This is the only step required to make the app work — add your API key here.**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and set your real Groq API key (get one free at
   https://console.groq.com/keys):
   ```
   GROQ_API_KEY=gsk_your_real_key_here
   ```
3. Leave the other values as their defaults unless you want to change the
   model or chunking behavior.

`.env` is already listed in `.gitignore` — it will never be committed.

## 9. Usage (Local)

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (usually `http://localhost:8501`), upload
a PDF or image, pick a summary detail level, and click **Analyze Document**.

## 10. Deployment (Streamlit Community Cloud)

1. Push this project to a **public GitHub repository** (`.env` will not be
   included, thanks to `.gitignore` — that's expected and correct).
2. Go to https://share.streamlit.io, sign in, and click **New app**.
3. Select your repo, branch, and set the main file path to `app.py`.
4. Before (or right after) deploying, open **Settings → Secrets** on the app
   and paste in (same values as your local `.env`, TOML format):
   ```toml
   GROQ_API_KEY = "gsk_your_real_key_here"
   GROQ_MODEL = "openai/gpt-oss-120b"
   EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
   ```
   (See `.streamlit/secrets.toml.example` for the exact format.)
5. Deploy. Streamlit Cloud automatically:
   - installs Python packages from `requirements.txt`
   - installs the `tesseract-ocr` system package from `packages.txt`
     (this is required for OCR to work in the cloud — without it, scanned
     PDFs and images will fail with a clear error message)
6. Once live, your app works identically to the local version — `config.py`
   automatically reads from Streamlit `secrets` on Cloud and from `.env`
   locally, so **no code changes are needed between environments**.

## 11. Limitations

- Single-document sessions only (no multi-document knowledge base or chat
  history persistence — by design, to keep scope tight)
- OCR quality depends on scan clarity; very low-quality scans may extract
  poorly
- Very large documents are summarized via map-reduce, which trades a small
  amount of nuance for staying within the LLM's context window
- No user authentication or accounts

## 12. Future Improvements

- Multi-document knowledge bases with cross-document Q&A
- Persistent chat history per document
- Support for DOCX and TXT uploads
- Streaming LLM responses in the UI
- Configurable chunk size / retrieval count from the UI

## 13. 200-Word Approach Summary

Document-Summarizer ingests a PDF or image, and extracts its text using
PyMuPDF for digital PDFs or Tesseract OCR for scanned pages and images,
automatically detecting which path a given page needs. Extracted text is
cleaned, normalized, and split into overlapping chunks while preserving page
numbers, then converted into semantic embeddings via a Sentence-Transformers
model and indexed in a FAISS vector store. For summarization, the app sends
the full document (or, for large documents, a map-reduce hierarchy of
section summaries) to a Groq-hosted LLM with a prompt instructing it to scale
summary length to the content's actual length and complexity rather than a
fixed word count. The same LLM call pattern produces bullet-point key points,
concise topic-heading "main ideas" for active recall, and structured
improvement suggestions. For interactive Q&A, user questions are embedded and
matched against the FAISS index to retrieve the most relevant chunks, which
are passed to the LLM as grounding context so answers are traceable to
specific pages rather than hallucinated. The entire pipeline runs inside a
single Streamlit app with clear loading states and error handling, and
deploys unchanged to Streamlit Community Cloud via `requirements.txt`,
`packages.txt`, and Streamlit Secrets.
