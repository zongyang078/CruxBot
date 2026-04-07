"""
CruxBot — Chunking Pipeline
=============================
Splits unified documents into RAG-ready chunks.
 
Chunking rules:
  - Routes: pass-through if short (<300 tokens), else split at 300t / 50t overlap
  - Forum/Reddit: split at 400 tokens / 75 token overlap
  - Articles (AAC): split at 500 tokens / 100 token overlap
  - Gear reviews: split at 350 tokens / 50 token overlap
 
Each chunk inherits all parent metadata and gets chunk_id, chunk_index, total_chunks.
 
Input:  data/unified/cruxbot_unified.json
Output: data/chunks/cruxbot_chunks.json
 
Usage:
    python -u scripts/05_chunk.py
"""
 
import json
import os
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter
 
# ============================================================
# Configuration
# ============================================================
INPUT_PATH  = "data/unified/cruxbot_unified.json"
OUTPUT_DIR  = "data/chunks"
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "cruxbot_chunks.json")
 
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
# Approximate chars-per-token for typical English text.
# all-MiniLM-L6-v2 uses a WordPiece tokenizer; ~4 chars/token is a safe estimate.
CHARS_PER_TOKEN = 4
 
# Per-content-type chunk settings: (chunk_tokens, overlap_tokens)
CHUNK_CONFIG = {
    "route":            (300,  50),
    "forum_discussion": (400,  75),
    "reddit_post":      (400,  75),
    "article":          (500, 100),
    "gear_review":      (350,  50),
}
DEFAULT_CHUNK = (400, 75)
 
# Routes shorter than this (in chars) are passed through as a single chunk
ROUTE_PASSTHROUGH_CHARS = 300 * CHARS_PER_TOKEN   # ~1200 chars
 
# Build a splitter for a given content type
def get_splitter(content_type: str) -> RecursiveCharacterTextSplitter:
    chunk_tokens, overlap_tokens = CHUNK_CONFIG.get(content_type, DEFAULT_CHUNK)
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_tokens * CHARS_PER_TOKEN,
        chunk_overlap=overlap_tokens * CHARS_PER_TOKEN,
        length_function=len,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )
 
# Chunk a single document
def chunk_document(doc: dict) -> list[dict]:
    """
    Split one unified document into one or more chunk dicts.
    Each chunk is a superset of the parent doc's fields plus:
      chunk_id, chunk_index, total_chunks, parent_doc_id
    """
    content_type = doc.get("content_type", "article")
    text = doc.get("text", "").strip()
    doc_id = doc["doc_id"]
 
    # Short route pass-through, no splitting needed
    if content_type == "route" and len(text) <= ROUTE_PASSTHROUGH_CHARS:
        chunk = {**doc, "chunk_id": f"{doc_id}_c0", "chunk_index": 0, "total_chunks": 1, "parent_doc_id": doc_id}
        return [chunk]
 
    splitter = get_splitter(content_type)
    splits = splitter.split_text(text)
 
    # Guard: splitter occasionally returns empty strings
    splits = [s.strip() for s in splits if s.strip()]
    if not splits:
        return []
 
    chunks = []
    for i, split_text in enumerate(splits):
        chunk = {
            **doc,
            "text":          split_text,
            "chunk_id":      f"{doc_id}_c{i}",
            "chunk_index":   i,
            "total_chunks":  len(splits),
            "parent_doc_id": doc_id,
        }
        chunks.append(chunk)
 
    return chunks
 
# Main pipeline
def main():
    print(f"   Input:  {INPUT_PATH}")
    print(f"   Output: {OUTPUT_PATH}")
    print(f"   Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
 
    # Load
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        documents = json.load(f)
    print(f"  Loaded {len(documents):,} documents")
 
    # Chunk
    all_chunks = []
    skipped = 0
    passthrough = 0
    type_stats: dict[str, dict] = {}
 
    for i, doc in enumerate(documents):
        chunks = chunk_document(doc)
        if not chunks:
            skipped += 1
            continue
 
        ct = doc.get("content_type", "unknown")
        if ct not in type_stats:
            type_stats[ct] = {"docs": 0, "chunks": 0}
        type_stats[ct]["docs"]   += 1
        type_stats[ct]["chunks"] += len(chunks)
 
        if len(chunks) == 1 and doc.get("content_type") == "route":
            passthrough += 1
 
        all_chunks.extend(chunks)
 
        if (i + 1) % 10_000 == 0:
            print(f"  Processed {i+1:,}/{len(documents):,} docs → {len(all_chunks):,} chunks so far...")
 
    print(f"\n  Done. {len(documents):,} docs: {len(all_chunks):,} chunks ({skipped} skipped, {passthrough} route pass-throughs)")
 
    # Stats by content type
    print(f"\n  Chunk breakdown by content type:")
    print(f"  {'Content type':<25} {'Docs':>8} {'Chunks':>8} {'Avg chunks/doc':>15}")
    print(f"  {'-'*60}")
    for ct, stats in sorted(type_stats.items(), key=lambda x: -x[1]["chunks"]):
        avg = stats["chunks"] / max(stats["docs"], 1)
        print(f"  {ct:<25} {stats['docs']:>8,} {stats['chunks']:>8,} {avg:>14.1f}x")
 
    # Text length distribution across chunks
    lengths = [len(c["text"]) for c in all_chunks]
    avg_len = sum(lengths) / max(len(lengths), 1)
    print(f"\n  Chunk text length (chars):")
    print(f"    Min:     {min(lengths):>8,}")
    print(f"    Max:     {max(lengths):>8,}")
    print(f"    Average: {avg_len:>8,.0f}")
    print(f"    <200:    {sum(1 for l in lengths if l < 200):>8,}")
    print(f"    200-800: {sum(1 for l in lengths if 200 <= l < 800):>8,}")
    print(f"    800+:    {sum(1 for l in lengths if l >= 800):>8,}")
 
    # Save
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2, default=str)
    size_mb = os.path.getsize(OUTPUT_PATH) / 1024 / 1024
    print(f"  Saved {len(all_chunks):,} chunks: {OUTPUT_PATH} ({size_mb:.1f} MB)")
 
 
if __name__ == "__main__":
    main()