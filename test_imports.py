print("Starting...")

print("Testing vector_store...")
from utils.vector_store import FAISSVectorStore
print("vector_store OK")

print("Testing summarizer...")
from utils.summarizer import (
    generate_improvement_suggestions,
    generate_key_points,
    generate_main_ideas,
    generate_summary,
)
print("summarizer OK")

print("Testing RAG...")
from utils.rag import answer_question
print("RAG OK")

print("ALL IMPORTS SUCCESSFUL")