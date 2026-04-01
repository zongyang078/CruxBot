import json
import urllib.request
from src.retrieval import retrieve

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


def _build_prompt(query: str, chunks: list[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[{i}] {chunk['text']}")
    context = "\n\n".join(context_parts)

    return (
        "You are CruxBot, an expert rock climbing assistant. "
        "Answer the user's question using ONLY the context below. "
        "If the context does not contain enough information to answer, "
        'say exactly: "I don\'t have data on this."\n\n'
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer (cite sources by number, e.g. [1], [2]):"
    )


def _call_ollama(prompt: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read())
    return body["response"].strip()


def answer(query: str, top_k: int = 5, chroma_path: str = "./chroma_db") -> dict:
    """
    Run the full RAG pipeline for a query.

    Returns:
        {
            "query": str,
            "answer": str,
            "sources": [{"url": str, "text_snippet": str}, ...]
        }
    """
    chunks = retrieve(query, top_k=top_k, chroma_path=chroma_path)
    prompt = _build_prompt(query, chunks)
    response = _call_ollama(prompt)

    sources = [
        {"url": c["source_url"], "text_snippet": c["text"][:120]}
        for c in chunks
        if c["source_url"]
    ]

    return {
        "query": query,
        "answer": response,
        "sources": sources,
    }
