# """
# Document-Summarizer
# AI-Powered Document Summary Assistant

# Pipeline:
#   Upload (PDF/Image) -> Extract/OCR -> Clean & Chunk -> Embed -> FAISS
#   -> Summary + Key Points + Main Ideas + Improvement Suggestions
#   -> RAG Q&A

# Run locally:   streamlit run app.py
# Deployed on:   Streamlit Community Cloud
# """

# import io

# import streamlit as st
# from PIL import Image

# from config import GROQ_API_KEY, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
# from utils import pdf_extractor, text_processor
# from utils.groq_client import GroqGenerationError, GroqNotConfiguredError
# from utils.ocr import OCRError, ocr_image
# from utils.rag import answer_question
# from utils.summarizer import (
#     generate_improvement_suggestions,
#     generate_key_points,
#     generate_main_ideas,
#     generate_summary,
# )
# from utils.vector_store import FAISSVectorStore

# st.write("DEBUG: imports completed")

# st.set_page_config(
#     page_title="Document-Summarizer",
#     page_icon="📄",
#     layout="centered",
# )

# # ---------------------------------------------------------------------------
# # Session state
# # ---------------------------------------------------------------------------
# DEFAULTS = {
#     "processed": False,
#     "file_name": None,
#     "num_pages": None,
#     "full_text": "",
#     "vector_store": None,
#     "summary": "",
#     "key_points": "",
#     "main_ideas": "",
#     "suggestions": "",
#     "qa_history": [],  # list of {"question": str, "answer": str, "sources": list}
# }
# for key, value in DEFAULTS.items():
#     if key not in st.session_state:
#         st.session_state[key] = value


# def reset_state():
#     for key, value in DEFAULTS.items():
#         st.session_state[key] = value


# # ---------------------------------------------------------------------------
# # Pipeline
# # ---------------------------------------------------------------------------
# def extract_pages(file_bytes: bytes, extension: str):
#     """Returns list of {"page": int, "text": str} using the dual-path extraction system."""
#     if extension == "pdf":
#         doc = pdf_extractor.open_pdf(file_bytes)
#         raw_pages = pdf_extractor.extract_text_per_page(doc)

#         pages = []
#         ocr_progress = st.empty()
#         for i, page in enumerate(raw_pages):
#             if page.needs_ocr:
#                 ocr_progress.info(f"🔄 OCR'ing page {page.page_number} (no embedded text found)...")
#                 try:
#                     image = pdf_extractor.render_page_as_image(doc, i)
#                     text = ocr_image(image)
#                 except OCRError as e:
#                     st.warning(f"⚠️ Page {page.page_number}: {e}")
#                     text = ""
#             else:
#                 text = page.text
#             pages.append({"page": page.page_number, "text": text_processor.clean_text(text)})
#         ocr_progress.empty()
#         doc.close()
#         return pages

#     else:  # image types: png, jpg, jpeg
#         image_text = ocr_image(Image.open(io.BytesIO(file_bytes)))
#         return [{"page": 1, "text": text_processor.clean_text(image_text)}]


# def run_pipeline(uploaded_file, detail_level: str):
#     extension = uploaded_file.name.split(".")[-1].lower()
#     file_bytes = uploaded_file.getvalue()

#     if extension not in SUPPORTED_EXTENSIONS:
#         st.error("❌ Unsupported file type. Please upload PDF, PNG, JPG or JPEG.")
#         return

#     if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
#         st.error(f"❌ File too large. Please upload a file under {MAX_FILE_SIZE_MB} MB.")
#         return

#     step = st.status("Processing document...", expanded=True)

#     try:
#         step.write("🔄 Extracting text...")
#         try:
#             pages = extract_pages(file_bytes, extension)
#         except OCRError as e:
#             step.update(label="Extraction failed", state="error")
#             st.error(f"⚠️ {e}")
#             return

#         full_text = text_processor.build_full_text(pages)
#         if not full_text.strip():
#             step.update(label="No text found", state="error")
#             st.error("⚠️ No readable text could be extracted. Please upload a clearer document.")
#             return
#         step.write("✓ Text extracted")

#         if len(full_text) > 12000:
#             step.write("⚠️ Large document detected. Processing it in multiple sections.")

#         step.write("🔄 Creating document chunks...")
#         chunks = text_processor.chunk_pages(pages)
#         step.write(f"✓ {len(chunks)} chunks created")

#         step.write("🔄 Building semantic index...")
#         vector_store = FAISSVectorStore()
#         vector_store.build(chunks)
#         step.write("✓ FAISS index ready")

#         step.write("🔄 Generating analysis (summary, key points, main ideas, suggestions)...")
#         summary = generate_summary(full_text, detail_level=detail_level)
#         key_points = generate_key_points(full_text)
#         main_ideas = generate_main_ideas(full_text)
#         suggestions = generate_improvement_suggestions(full_text)
#         step.write("✓ Summary generated")

#         st.session_state.processed = True
#         st.session_state.file_name = uploaded_file.name
#         st.session_state.num_pages = len(pages)
#         st.session_state.full_text = full_text
#         st.session_state.vector_store = vector_store
#         st.session_state.summary = summary
#         st.session_state.key_points = key_points
#         st.session_state.main_ideas = main_ideas
#         st.session_state.suggestions = suggestions
#         st.session_state.qa_history = []

#         step.update(label="✅ Analysis complete", state="complete", expanded=False)

#     except GroqNotConfiguredError as e:
#         step.update(label="Configuration needed", state="error")
#         st.error(f"❌ {e}")
#     except GroqGenerationError as e:
#         step.update(label="Generation failed", state="error")
#         st.error(str(e))
#     except Exception as e:
#         step.update(label="Unexpected error", state="error")
#         st.error(f"❌ Something went wrong: {e}")


# def build_download_text() -> str:
#     return (
#         f"DOCUMENT: {st.session_state.file_name}\n"
#         f"PAGES: {st.session_state.num_pages}\n\n"
#         f"=== SUMMARY ===\n{st.session_state.summary}\n\n"
#         f"=== KEY POINTS ===\n{st.session_state.key_points}\n\n"
#         f"=== MAIN IDEAS ===\n{st.session_state.main_ideas}\n\n"
#         f"=== IMPROVEMENT SUGGESTIONS ===\n{st.session_state.suggestions}\n"
#     )


# # ---------------------------------------------------------------------------
# # UI
# # ---------------------------------------------------------------------------
# st.title("📄 AI Document Summary Assistant")
# st.caption("Upload → Extract/OCR → Summarize → Ask")

# if not GROQ_API_KEY:
#     st.warning(
#         "⚠️ GROQ_API_KEY is not configured yet. Add it to a local `.env` file, or to "
#         "this app's Secrets on Streamlit Community Cloud, before analyzing a document. "
#         "See the README for exact steps.",
#         icon="🔑",
#     )

# with st.container(border=True):
#     uploaded_file = st.file_uploader(
#         "📤 Upload your document",
#         type=SUPPORTED_EXTENSIONS,
#         help="PDF, PNG, JPG or JPEG — including scanned documents.",
#     )
#     detail_level = st.selectbox("Summary Detail", ["Short", "Medium", "Long"], index=1)
#     analyze_clicked = st.button("Analyze Document", type="primary", use_container_width=True)

# if analyze_clicked:
#     if uploaded_file is None:
#         st.error("Please upload a document first.")
#     else:
#         reset_state()
#         run_pipeline(uploaded_file, detail_level)

# # ---------------------------------------------------------------------------
# # Results
# # ---------------------------------------------------------------------------
# if st.session_state.processed:
#     st.divider()
#     st.subheader(f"📄 Document: {st.session_state.file_name}")
#     st.caption(f"Pages: {st.session_state.num_pages} | Extracted successfully")

#     st.markdown("### 📝 Summary")
#     st.write(st.session_state.summary)

#     st.markdown("### 🔑 Key Points")
#     st.markdown(st.session_state.key_points)

#     st.markdown("### 🎯 Main Ideas")
#     st.markdown(st.session_state.main_ideas)

#     st.markdown("### 💡 Improvement Suggestions")
#     st.markdown(st.session_state.suggestions)

#     st.divider()
#     st.markdown("### 💬 Ask Your Document")
#     with st.form("qa_form", clear_on_submit=True):
#         question = st.text_input("Ask something about this document...")
#         ask_clicked = st.form_submit_button("Ask")

#     if ask_clicked and question.strip():
#         with st.spinner("🔄 Searching the document and generating an answer..."):
#             try:
#                 result = answer_question(question, st.session_state.vector_store)
#                 st.session_state.qa_history.insert(
#                     0, {"question": question, "answer": result["answer"], "sources": result["sources"]}
#                 )
#             except GroqNotConfiguredError as e:
#                 st.error(f"❌ {e}")
#             except GroqGenerationError as e:
#                 st.error(str(e))

#     for qa in st.session_state.qa_history:
#         with st.container(border=True):
#             st.markdown(f"**Q: {qa['question']}**")
#             st.write(qa["answer"])
#             if qa["sources"]:
#                 sources_str = ", ".join(f"Page {p}" for p in qa["sources"])
#                 st.caption(f"Sources: {sources_str}")

#     st.divider()
#     st.download_button(
#         "⬇ Download Summary",
#         data=build_download_text(),
#         file_name=f"{st.session_state.file_name}_summary.txt",
#         mime="text/plain",
#         use_container_width=True,
#     )



# """
# Document-Summarizer
# AI-Powered Document Summary Assistant

# Pipeline:
#   Upload (PDF/Image) -> Extract/OCR -> Clean & Chunk -> Embed -> FAISS
#   -> Summary + Key Points + Main Ideas + Improvement Suggestions
#   -> RAG Q&A

# Run locally:   streamlit run app.py
# Deployed on:   Streamlit Community Cloud
# """

# import io

# import streamlit as st
# from PIL import Image

# from config import GROQ_API_KEY, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
# from utils import pdf_extractor, text_processor
# from utils.groq_client import GroqGenerationError, GroqNotConfiguredError
# from utils.ocr import OCRError, ocr_image
# from utils.rag import answer_question
# from utils.summarizer import (
#     generate_improvement_suggestions,
#     generate_key_points,
#     generate_main_ideas,
#     generate_summary,
# )
# from utils.vector_store import FAISSVectorStore

# st.set_page_config(
#     page_title="Document-Summarizer",
#     page_icon="📄",
#     layout="centered",  # keeps content readable on mobile; avoid "wide" here
# )

# # ---------------------------------------------------------------------------
# # Responsive styling
# # A small CSS layer for mobile-friendly title sizing and spacing.
# # Uses a @media breakpoint so text shrinks gracefully on narrow (phone) screens
# # instead of wrapping awkwardly or forcing horizontal scroll.
# # ---------------------------------------------------------------------------
# st.markdown(
#     """
#     <style>
#         .main-title {
#             text-align: center;
#             font-size: 2.2rem;
#             font-weight: 700;
#             margin-bottom: 0.25rem;
#         }

#         .subtitle {
#             text-align: center;
#             color: #666;
#             margin-bottom: 1.5rem;
#         }

#         /* Any custom elements should use max-width + 100% width, never a
#            fixed pixel width, so nothing forces horizontal scrolling on phones. */
#         .app-block {
#             max-width: 900px;
#             width: 100%;
#             margin: 0 auto;
#         }

#         @media (max-width: 768px) {
#             .main-title {
#                 font-size: 1.6rem;
#             }

#             .subtitle {
#                 font-size: 0.9rem;
#             }
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # ---------------------------------------------------------------------------
# # Session state
# # ---------------------------------------------------------------------------
# DEFAULTS = {
#     "processed": False,
#     "file_name": None,
#     "num_pages": None,
#     "full_text": "",
#     "vector_store": None,
#     "summary": "",
#     "key_points": "",
#     "main_ideas": "",
#     "suggestions": "",
#     "qa_history": [],  # list of {"question": str, "answer": str, "sources": list}
# }
# for key, value in DEFAULTS.items():
#     if key not in st.session_state:
#         st.session_state[key] = value


# def reset_state():
#     for key, value in DEFAULTS.items():
#         st.session_state[key] = value


# # ---------------------------------------------------------------------------
# # Pipeline
# # ---------------------------------------------------------------------------
# def extract_pages(file_bytes: bytes, extension: str):
#     """Returns list of {"page": int, "text": str} using the dual-path extraction system."""
#     if extension == "pdf":
#         doc = pdf_extractor.open_pdf(file_bytes)
#         raw_pages = pdf_extractor.extract_text_per_page(doc)

#         pages = []
#         ocr_progress = st.empty()
#         for i, page in enumerate(raw_pages):
#             if page.needs_ocr:
#                 ocr_progress.info(f"🔄 OCR'ing page {page.page_number} (no embedded text found)...")
#                 try:
#                     image = pdf_extractor.render_page_as_image(doc, i)
#                     text = ocr_image(image)
#                 except OCRError as e:
#                     st.warning(f"⚠️ Page {page.page_number}: {e}")
#                     text = ""
#             else:
#                 text = page.text
#             pages.append({"page": page.page_number, "text": text_processor.clean_text(text)})
#         ocr_progress.empty()
#         doc.close()
#         return pages

#     else:  # image types: png, jpg, jpeg
#         image_text = ocr_image(Image.open(io.BytesIO(file_bytes)))
#         return [{"page": 1, "text": text_processor.clean_text(image_text)}]


# def run_pipeline(uploaded_file, detail_level: str):
#     extension = uploaded_file.name.split(".")[-1].lower()
#     file_bytes = uploaded_file.getvalue()

#     if extension not in SUPPORTED_EXTENSIONS:
#         st.error("❌ Unsupported file type. Please upload PDF, PNG, JPG or JPEG.")
#         return

#     if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
#         st.error(f"❌ File too large. Please upload a file under {MAX_FILE_SIZE_MB} MB.")
#         return

#     step = st.status("Processing document...", expanded=True)

#     try:
#         step.write("🔄 Extracting text...")
#         try:
#             pages = extract_pages(file_bytes, extension)
#         except OCRError as e:
#             step.update(label="Extraction failed", state="error")
#             st.error(f"⚠️ {e}")
#             return

#         full_text = text_processor.build_full_text(pages)
#         if not full_text.strip():
#             step.update(label="No text found", state="error")
#             st.error("⚠️ No readable text could be extracted. Please upload a clearer document.")
#             return
#         step.write("✓ Text extracted")

#         if len(full_text) > 12000:
#             step.write("⚠️ Large document detected. Processing it in multiple sections.")

#         step.write("🔄 Creating document chunks...")
#         chunks = text_processor.chunk_pages(pages)
#         step.write(f"✓ {len(chunks)} chunks created")

#         step.write("🔄 Building semantic index...")
#         vector_store = FAISSVectorStore()
#         vector_store.build(chunks)
#         step.write("✓ FAISS index ready")

#         step.write("🔄 Generating analysis (summary, key points, main ideas, suggestions)...")
#         summary = generate_summary(full_text, detail_level=detail_level)
#         key_points = generate_key_points(full_text)
#         main_ideas = generate_main_ideas(full_text)
#         suggestions = generate_improvement_suggestions(full_text)
#         step.write("✓ Summary generated")

#         st.session_state.processed = True
#         st.session_state.file_name = uploaded_file.name
#         st.session_state.num_pages = len(pages)
#         st.session_state.full_text = full_text
#         st.session_state.vector_store = vector_store
#         st.session_state.summary = summary
#         st.session_state.key_points = key_points
#         st.session_state.main_ideas = main_ideas
#         st.session_state.suggestions = suggestions
#         st.session_state.qa_history = []

#         step.update(label="✅ Analysis complete", state="complete", expanded=False)

#     except GroqNotConfiguredError as e:
#         step.update(label="Configuration needed", state="error")
#         st.error(f"❌ {e}")
#     except GroqGenerationError as e:
#         step.update(label="Generation failed", state="error")
#         st.error(str(e))
#     except Exception as e:
#         step.update(label="Unexpected error", state="error")
#         st.error(f"❌ Something went wrong: {e}")


# def build_download_text() -> str:
#     return (
#         f"DOCUMENT: {st.session_state.file_name}\n"
#         f"PAGES: {st.session_state.num_pages}\n\n"
#         f"=== SUMMARY ===\n{st.session_state.summary}\n\n"
#         f"=== KEY POINTS ===\n{st.session_state.key_points}\n\n"
#         f"=== MAIN IDEAS ===\n{st.session_state.main_ideas}\n\n"
#         f"=== IMPROVEMENT SUGGESTIONS ===\n{st.session_state.suggestions}\n"
#     )


# # ---------------------------------------------------------------------------
# # UI
# # ---------------------------------------------------------------------------
# st.markdown(
#     '<div class="main-title">📄 AI Document Summary Assistant</div>',
#     unsafe_allow_html=True,
# )
# st.markdown(
#     '<div class="subtitle">Upload → Extract/OCR → Summarize → Ask</div>',
#     unsafe_allow_html=True,
# )

# if not GROQ_API_KEY:
#     st.warning(
#         "⚠️ GROQ_API_KEY is not configured yet. Add it to a local `.env` file, or to "
#         "this app's Secrets on Streamlit Community Cloud, before analyzing a document. "
#         "See the README for exact steps.",
#         icon="🔑",
#     )

# with st.container(border=True):
#     st.subheader("📤 Upload Document")

#     # Deliberately stacked (not st.columns) — side-by-side controls get cramped
#     # on phone-width screens, so upload, detail level, and the button each get
#     # their own full-width row.
#     uploaded_file = st.file_uploader(
#         "PDF or Image",
#         type=SUPPORTED_EXTENSIONS,
#         help="PDF, PNG, JPG or JPEG — including scanned documents.",
#     )
#     detail_level = st.selectbox("Summary Detail", ["Short", "Medium", "Long"], index=1)
#     analyze_clicked = st.button("Analyze Document", type="primary", use_container_width=True)

# if analyze_clicked:
#     if uploaded_file is None:
#         st.error("Please upload a document first.")
#     else:
#         reset_state()
#         run_pipeline(uploaded_file, detail_level)

# # ---------------------------------------------------------------------------
# # Results
# # ---------------------------------------------------------------------------
# if st.session_state.processed:
#     st.divider()
#     st.subheader(f"📄 Document: {st.session_state.file_name}")
#     st.caption(f"Pages: {st.session_state.num_pages} | Extracted successfully")

#     st.markdown("### 📝 Summary")
#     st.write(st.session_state.summary)

#     st.markdown("### 🔑 Key Points")
#     st.markdown(st.session_state.key_points)

#     st.markdown("### 🎯 Main Ideas")
#     st.markdown(st.session_state.main_ideas)

#     st.markdown("### 💡 Improvement Suggestions")
#     st.markdown(st.session_state.suggestions)

#     # Collapsed by default — the full extracted text can be long, so it stays
#     # out of the way until someone actually wants to see it (mobile-friendly).
#     with st.expander("📑 View Extracted Text"):
#         st.text(st.session_state.full_text)

#     st.divider()
#     st.markdown("### 💬 Ask Your Document")
#     with st.form("qa_form", clear_on_submit=True):
#         question = st.text_input("Ask something about this document...")
#         ask_clicked = st.form_submit_button("Ask")

#     if ask_clicked and question.strip():
#         with st.spinner("🔄 Searching the document and generating an answer..."):
#             try:
#                 result = answer_question(question, st.session_state.vector_store)
#                 st.session_state.qa_history.insert(
#                     0, {"question": question, "answer": result["answer"], "sources": result["sources"]}
#                 )
#             except GroqNotConfiguredError as e:
#                 st.error(f"❌ {e}")
#             except GroqGenerationError as e:
#                 st.error(str(e))

#     for qa in st.session_state.qa_history:
#         with st.container(border=True):
#             st.markdown(f"**Q: {qa['question']}**")
#             st.write(qa["answer"])
#             if qa["sources"]:
#                 sources_str = ", ".join(f"Page {p}" for p in qa["sources"])
#                 with st.expander(f"📚 Sources ({sources_str})"):
#                     st.write(f"This answer was grounded in content from: {sources_str}")

#     st.divider()
#     st.download_button(
#         "⬇ Download Summary",
#         data=build_download_text(),
#         file_name=f"{st.session_state.file_name}_summary.txt",
#         mime="text/plain",
#         use_container_width=True,
#     )


"""
Document-Summarizer
AI-Powered Document Summary Assistant

Pipeline:
  Upload (PDF/Image) -> Extract/OCR -> Clean & Chunk -> Embed -> FAISS
  -> Summary + Key Points + Main Ideas + Improvement Suggestions
  -> RAG Q&A

Run locally:   streamlit run app.py
Deployed on:   Streamlit Community Cloud
"""

import io

import streamlit as st
from PIL import Image

from config import GROQ_API_KEY, MAX_FILE_SIZE_MB, SUPPORTED_EXTENSIONS
from utils import pdf_extractor, text_processor
from utils.groq_client import GroqGenerationError, GroqNotConfiguredError
from utils.ocr import OCRError, SUPPORTED_LANGUAGES, ocr_image
from utils.rag import answer_question
from utils.summarizer import (
    generate_improvement_suggestions,
    generate_key_points,
    generate_main_ideas,
    generate_summary,
)
from utils.vector_store import FAISSVectorStore

st.set_page_config(
    page_title="Document-Summarizer",
    page_icon="📄",
    layout="centered",  # keeps content readable on mobile; avoid "wide" here
)

# ---------------------------------------------------------------------------
# Responsive styling
# A small CSS layer for mobile-friendly title sizing and spacing.
# Uses a @media breakpoint so text shrinks gracefully on narrow (phone) screens
# instead of wrapping awkwardly or forcing horizontal scroll.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .main-title {
            text-align: center;
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 1.5rem;
        }

        /* Any custom elements should use max-width + 100% width, never a
           fixed pixel width, so nothing forces horizontal scrolling on phones. */
        .app-block {
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
        }

        @media (max-width: 768px) {
            .main-title {
                font-size: 1.6rem;
            }

            .subtitle {
                font-size: 0.9rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
DEFAULTS = {
    "processed": False,
    "file_name": None,
    "num_pages": None,
    "full_text": "",
    "vector_store": None,
    "summary": "",
    "key_points": "",
    "main_ideas": "",
    "suggestions": "",
    "qa_history": [],  # list of {"question": str, "answer": str, "sources": list}
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def reset_state():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def extract_pages(file_bytes: bytes, extension: str, ocr_lang: str):
    """Returns list of {"page": int, "text": str} using the dual-path extraction system."""
    if extension == "pdf":
        doc = pdf_extractor.open_pdf(file_bytes)
        raw_pages = pdf_extractor.extract_text_per_page(doc)

        pages = []
        ocr_progress = st.empty()
        for i, page in enumerate(raw_pages):
            if page.needs_ocr:
                ocr_progress.info(f"🔄 OCR'ing page {page.page_number} (no embedded text found)...")
                try:
                    image = pdf_extractor.render_page_as_image(doc, i)
                    text = ocr_image(image, lang=ocr_lang)
                except OCRError as e:
                    st.warning(f"⚠️ Page {page.page_number}: {e}")
                    text = ""
            else:
                text = page.text
            pages.append({"page": page.page_number, "text": text_processor.clean_text(text)})
        ocr_progress.empty()
        doc.close()
        return pages

    else:  # image types: png, jpg, jpeg
        image_text = ocr_image(Image.open(io.BytesIO(file_bytes)), lang=ocr_lang)
        return [{"page": 1, "text": text_processor.clean_text(image_text)}]


def run_pipeline(uploaded_file, detail_level: str, ocr_lang: str):
    extension = uploaded_file.name.split(".")[-1].lower()
    file_bytes = uploaded_file.getvalue()

    if extension not in SUPPORTED_EXTENSIONS:
        st.error("❌ Unsupported file type. Please upload PDF, PNG, JPG or JPEG.")
        return

    if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        st.error(f"❌ File too large. Please upload a file under {MAX_FILE_SIZE_MB} MB.")
        return

    step = st.status("Processing document...", expanded=True)

    try:
        step.write("🔄 Extracting text...")
        try:
            pages = extract_pages(file_bytes, extension, ocr_lang)
        except OCRError as e:
            step.update(label="Extraction failed", state="error")
            st.error(f"⚠️ {e}")
            return

        full_text = text_processor.build_full_text(pages)
        if not full_text.strip():
            step.update(label="No text found", state="error")
            st.error("⚠️ No readable text could be extracted. Please upload a clearer document.")
            return
        step.write("✓ Text extracted")

        if len(full_text) > 12000:
            step.write("⚠️ Large document detected. Processing it in multiple sections.")

        step.write("🔄 Creating document chunks...")
        chunks = text_processor.chunk_pages(pages)
        step.write(f"✓ {len(chunks)} chunks created")

        step.write("🔄 Building semantic index...")
        vector_store = FAISSVectorStore()
        vector_store.build(chunks)
        step.write("✓ FAISS index ready")

        step.write("🔄 Generating analysis (summary, key points, main ideas, suggestions)...")
        summary = generate_summary(full_text, detail_level=detail_level)
        key_points = generate_key_points(full_text)
        main_ideas = generate_main_ideas(full_text)
        suggestions = generate_improvement_suggestions(full_text)
        step.write("✓ Summary generated")

        st.session_state.processed = True
        st.session_state.file_name = uploaded_file.name
        st.session_state.num_pages = len(pages)
        st.session_state.full_text = full_text
        st.session_state.vector_store = vector_store
        st.session_state.summary = summary
        st.session_state.key_points = key_points
        st.session_state.main_ideas = main_ideas
        st.session_state.suggestions = suggestions
        st.session_state.qa_history = []

        step.update(label="✅ Analysis complete", state="complete", expanded=False)

    except GroqNotConfiguredError as e:
        step.update(label="Configuration needed", state="error")
        st.error(f"❌ {e}")
    except GroqGenerationError as e:
        step.update(label="Generation failed", state="error")
        st.error(str(e))
    except Exception as e:
        step.update(label="Unexpected error", state="error")
        st.error(f"❌ Something went wrong: {e}")


def build_download_text() -> str:
    return (
        f"DOCUMENT: {st.session_state.file_name}\n"
        f"PAGES: {st.session_state.num_pages}\n\n"
        f"=== SUMMARY ===\n{st.session_state.summary}\n\n"
        f"=== KEY POINTS ===\n{st.session_state.key_points}\n\n"
        f"=== MAIN IDEAS ===\n{st.session_state.main_ideas}\n\n"
        f"=== IMPROVEMENT SUGGESTIONS ===\n{st.session_state.suggestions}\n"
    )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-title">📄 AI Document Summary Assistant</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Upload → Extract/OCR → Summarize → Ask</div>',
    unsafe_allow_html=True,
)

if not GROQ_API_KEY:
    st.warning(
        "⚠️ GROQ_API_KEY is not configured yet. Add it to a local `.env` file, or to "
        "this app's Secrets on Streamlit Community Cloud, before analyzing a document. "
        "See the README for exact steps.",
        icon="🔑",
    )

with st.container(border=True):
    st.subheader("📤 Upload Document")

    # Deliberately stacked (not st.columns) — side-by-side controls get cramped
    # on phone-width screens, so upload, detail level, language, and the button
    # each get their own full-width row.
    uploaded_file = st.file_uploader(
        "PDF or Image",
        type=SUPPORTED_EXTENSIONS,
        help="PDF, PNG, JPG or JPEG — including scanned documents.",
    )
    
    lang_options = list(SUPPORTED_LANGUAGES.keys())
    default_idx = lang_options.index("hin+eng") if "hin+eng" in lang_options else 0

    ocr_lang_code = st.selectbox(
        label="Document Language (for OCR)",
        options=lang_options,
        index=default_idx,
        format_func=lambda code: SUPPORTED_LANGUAGES[code],
        help="Select the predominant language in the document/image to improve OCR accuracy."
    )
    
    detail_level = st.selectbox("Summary Detail", ["Short", "Medium", "Long"], index=1)
    analyze_clicked = st.button("Analyze Document", type="primary", use_container_width=True)

if analyze_clicked:
    if uploaded_file is None:
        st.error("Please upload a document first.")
    else:
        reset_state()
        run_pipeline(uploaded_file, detail_level, ocr_lang_code)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if st.session_state.processed:
    st.divider()
    st.subheader(f"📄 Document: {st.session_state.file_name}")
    st.caption(f"Pages: {st.session_state.num_pages} | Extracted successfully")

    st.markdown("### 📝 Summary")
    st.write(st.session_state.summary)

    st.markdown("### 🔑 Key Points")
    st.markdown(st.session_state.key_points)

    st.markdown("### 🎯 Main Ideas")
    st.markdown(st.session_state.main_ideas)

    st.markdown("### 💡 Improvement Suggestions")
    st.markdown(st.session_state.suggestions)

    # Collapsed by default — the full extracted text can be long, so it stays
    # out of the way until someone actually wants to see it (mobile-friendly).
    with st.expander("📑 View Extracted Text"):
        st.text(st.session_state.full_text)

    st.divider()
    st.markdown("### 💬 Ask Your Document")
    with st.form("qa_form", clear_on_submit=True):
        question = st.text_input("Ask something about this document...")
        ask_clicked = st.form_submit_button("Ask")

    if ask_clicked and question.strip():
        with st.spinner("🔄 Searching the document and generating an answer..."):
            try:
                result = answer_question(question, st.session_state.vector_store)
                st.session_state.qa_history.insert(
                    0, {"question": question, "answer": result["answer"], "sources": result["sources"]}
                )
            except GroqNotConfiguredError as e:
                st.error(f"❌ {e}")
            except GroqGenerationError as e:
                st.error(str(e))

    for qa in st.session_state.qa_history:
        with st.container(border=True):
            st.markdown(f"**Q: {qa['question']}**")
            st.write(qa["answer"])
            if qa["sources"]:
                sources_str = ", ".join(f"Page {p}" for p in qa["sources"])
                with st.expander(f"📚 Sources ({sources_str})"):
                    st.write(f"This answer was grounded in content from: {sources_str}")

    st.divider()
    st.download_button(
        "⬇ Download Summary",
        data=build_download_text(),
        file_name=f"{st.session_state.file_name}_summary.txt",
        mime="text/plain",
        use_container_width=True,
    )
