import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.Client()
collection = client.get_or_create_collection("capy_read_memory")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def store_reflection(book: str, reflection: str):
    embedding = embedder.encode([reflection])[0]
    collection.add(
        documents=[reflection],
        ids=[book + "_entry"],
        embeddings=[embedding]
    )

def search_reflections(query: str) -> list:
    embedding = embedder.encode([query])[0]
    results = collection.query(query_embeddings=[embedding], n_results=3)
    return results["documents"][0] if results.get("documents") else []
