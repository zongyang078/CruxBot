"""
End-to-end RAG test.

1. Builds a temporary ChromaDB from ~/cruxbot/data/mountain_routes.jsonl
2. Runs three climbing queries through retrieval + RAG pipeline
3. Prints retrieved chunks and (if Ollama is running) LLM answers

Usage:
    cd ~/cruxbot/CruxBot
    python -m tests.test_rag
"""

import json
import os
import sys
import tempfile

import chromadb
from sentence_transformers import SentenceTransformer

DATA_PATH = os.path.expanduser("~/cruxbot/data/mountain_routes.jsonl")
COLLECTION_NAME = "cruxbot"

QUERIES = [
    "How do I train for V4 bouldering?",
    "What gear do I need for trad climbing?",
    "Best sport climbing areas in the US?",
]


# ---------------------------------------------------------------------------
# Build test ChromaDB
# ---------------------------------------------------------------------------

def build_chroma(data_path: str, chroma_path: str, batch_size: int = 500) -> int:
    print(f"Loading data from {data_path} ...")
    records = []
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"  {len(records)} records loaded.")

    model = SentenceTransformer("all-MiniLM-L6-v2")

    client = chromadb.PersistentClient(path=chroma_path)
    # Drop and recreate so tests are reproducible
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    print("Embedding and indexing (this may take a minute) ...")
    for start in range(0, len(records), batch_size):
        batch = records[start: start + batch_size]
        texts = [r["text"] for r in batch]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        ids = [f"doc_{start + i}" for i in range(len(batch))]
        metadatas = [
            {
                "source_url": r.get("source_url", ""),
                "source_type": r.get("source_type", ""),
                "climbing_type": r.get("climbing_type", ""),
                "grade": r.get("grade", ""),
                "location": r.get("location", ""),
                "name": r.get("name", ""),
            }
            for r in batch
        ]
        collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        print(f"  indexed {min(start + batch_size, len(records))}/{len(records)}", end="\r")

    print(f"\nDone. {len(records)} documents indexed.")
    return len(records)


# ---------------------------------------------------------------------------
# Retrieval test
# ---------------------------------------------------------------------------

def test_retrieval(chroma_path: str):
    # Import here so the module picks up our temp chroma path
    import importlib
    import src.retrieval as ret_mod

    # Reset cached collection so it re-opens from our temp path
    ret_mod._collection = None

    print("\n" + "=" * 60)
    print("RETRIEVAL TEST")
    print("=" * 60)

    for query in QUERIES:
        print(f"\nQuery: {query}")
        chunks = ret_mod.retrieve(query, top_k=3, chroma_path=chroma_path)
        for i, c in enumerate(chunks, 1):
            snippet = c["text"][:100].replace("\n", " ")
            print(f"  [{i}] (score={c['score']:.4f}) {snippet}")
            print(f"       url: {c['source_url']}")


# ---------------------------------------------------------------------------
# RAG pipeline test (requires Ollama running)
# ---------------------------------------------------------------------------

def test_rag_pipeline(chroma_path: str):
    import src.retrieval as ret_mod
    import src.rag_pipeline as rag_mod

    ret_mod._collection = None  # reset so it uses temp path

    print("\n" + "=" * 60)
    print("RAG PIPELINE TEST  (requires Ollama + llama3)")
    print("=" * 60)

    for query in QUERIES:
        print(f"\nQ: {query}")
        try:
            result = rag_mod.answer(query, top_k=5, chroma_path=chroma_path)
            print(f"A: {result['answer']}")
            print("Sources:")
            for s in result["sources"]:
                print(f"  - {s['url']}")
        except Exception as e:
            print(f"  [SKIPPED — Ollama not available: {e}]")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Use a temp dir so we don't pollute the real chroma_db
    with tempfile.TemporaryDirectory(prefix="cruxbot_test_chroma_") as tmp:
        print(f"Temporary ChromaDB: {tmp}")
        build_chroma(DATA_PATH, tmp)
        test_retrieval(tmp)
        test_rag_pipeline(tmp)
        print("\nAll tests complete.")
