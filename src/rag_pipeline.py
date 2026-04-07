"""
CruxBot — RAG Pipeline (v3)
=============================
Improvements over v2:
  1. Streaming support — token-by-token output for Streamlit
  2. Domain-check prompt — rejects non-climbing questions before checking context
  3. Incidental mention guard — prevents using passing mentions for off-topic answers
  4. Keeps non-streaming answer() for evaluation script compatibility
"""

import json
import os
import urllib.request
from src.retrieval import retrieve, extract_grade_from_query, get_grade_equivalents, is_specific_url

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")


def _build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build a prompt with richer context blocks and a more nuanced instruction.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        header_parts = []
        if meta.get("content_type"):
            header_parts.append(f"Type: {meta['content_type']}")
        if meta.get("grade"):
            header_parts.append(f"Grade: {meta['grade']}")
        if meta.get("location"):
            loc = meta["location"]
            if len(loc) > 80:
                loc = loc[:80] + "..."
            header_parts.append(f"Location: {loc}")

        source_url = chunk.get("source_url", "")
        url_note = ""
        if source_url and not is_specific_url(source_url):
            url_note = " (general forum page, not a specific post)"
        if source_url:
            header_parts.append(f"URL: {source_url}{url_note}")

        header = " | ".join(header_parts)
        if header:
            context_parts.append(f"[{i}] ({header})\n{chunk['text']}")
        else:
            context_parts.append(f"[{i}] {chunk['text']}")

    context = "\n\n".join(context_parts)

    grade_note = ""
    grade = extract_grade_from_query(query)
    if grade:
        equivalents = get_grade_equivalents(grade)
        if len(equivalents) > 1:
            grade_note = (
                f"\nNote: The grade {grade} is approximately equivalent to: "
                f"{', '.join(equivalents)}. Consider these when matching routes.\n"
            )

    return (
        "You are CruxBot, an expert rock climbing assistant.\n\n"
        "INSTRUCTIONS:\n"
        "- FIRST, determine if the question is about rock climbing (routes, training, "
        "gear, safety, accidents, technique, or climbing areas). If the question is NOT about "
        "climbing at all (e.g., restaurants, hotels, cooking, sports scores, history, "
        'weather, coding), immediately respond: "I don\'t have data on this in my '
        'climbing knowledge base. I can only answer questions about rock climbing."\n'
        "- For climbing-related questions, answer based on the context below.\n"
        "- Cite sources by number (e.g., [1], [2]) when referencing specific information.\n"
        "- If the context contains relevant but incomplete information, provide what you "
        "can and note what is missing. Do NOT refuse entirely if partial information exists.\n"
        "- If the context contains NO relevant climbing information at all, say: "
        '"I don\'t have data on this in my climbing knowledge base."\n'
        "- NEVER make up facts, routes, grades, or URLs that are not in the context.\n"
        "- If the context only mentions a non-climbing topic in passing (e.g., a climber "
        "casually mentioning food or hotels), do NOT treat that as relevant information "
        "for non-climbing questions.\n"
        "- If a source URL is marked as a general forum page, mention that the "
        "specific post link is not available.\n"
        f"{grade_note}\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        "Answer:"
    )


# ============================================================
# Non-streaming call (used by evaluate.py)
# ============================================================

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


# ============================================================
# Streaming call (used by Streamlit)
# ============================================================

def _call_ollama_stream(prompt: str):
    """
    Generator that yields tokens one by one from Ollama streaming API.
    """
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
    }).encode()

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        for line in resp:
            if line:
                try:
                    chunk = json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue


# ============================================================
# Non-streaming answer (for evaluation script)
# ============================================================

def answer(query: str, top_k: int = 5, chroma_path: str = "data/chroma") -> dict:
    """
    Run the full RAG pipeline (non-streaming).
    Used by evaluate.py and other scripts.
    """
    from src.retrieval import detect_query_intent

    intent = detect_query_intent(query)
    chunks = retrieve(query, top_k=top_k, chroma_path=chroma_path)
    prompt = _build_prompt(query, chunks)
    response = _call_ollama(prompt)

    sources = []
    for c in chunks:
        url = c.get("source_url", "")
        if url:
            sources.append({
                "url": url,
                "text_snippet": c["text"][:120],
                "is_specific": c.get("source_url_specific", True),
            })

    return {
        "query": query,
        "answer": response,
        "sources": sources,
        "intent": intent,
    }


# ============================================================
# Streaming answer (for Streamlit)
# ============================================================

def answer_stream(query: str, top_k: int = 5, chroma_path: str = "data/chroma") -> dict:
    """
    Run RAG retrieval, return chunks/sources and a token generator.
    The LLM response is NOT called yet — the generator is lazy.

    Returns:
        {
            "query": str,
            "stream": generator yielding tokens,
            "sources": [...],
            "intent": str | None,
        }
    """
    from src.retrieval import detect_query_intent

    intent = detect_query_intent(query)
    chunks = retrieve(query, top_k=top_k, chroma_path=chroma_path)
    prompt = _build_prompt(query, chunks)

    sources = []
    for c in chunks:
        url = c.get("source_url", "")
        if url:
            sources.append({
                "url": url,
                "text_snippet": c["text"][:120],
                "is_specific": c.get("source_url_specific", True),
            })

    return {
        "query": query,
        "stream": _call_ollama_stream(prompt),
        "sources": sources,
        "intent": intent,
    }
