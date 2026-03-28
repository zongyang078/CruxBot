"""
CruxBot — Embedding Pipeline
==============================
Generates embeddings for all chunks and loads them into ChromaDB.

Model:   all-MiniLM-L6-v2 (384-dim, fast, good baseline)

Features:
  - Batched encoding for speed
  - Progress checkpointing: saves progress every CHECKPOINT_EVERY batches
    so a crash doesn't lose everything. Re-run resumes from last checkpoint
  - Local JSON backup of all embedded chunks (separate from ChromaDB)
  - ChromaDB upsert (idempotent, safe to re-run)

Input:   data/chunks/cruxbot_chunks.json
Outputs:
  data/embeddings/cruxbot_embedded.json   local backup (chunks + embeddings)
  data/embeddings/checkpoint.json         resume state
  data/chroma/                            ChromaDB persistent store

Usage:
    python -u scripts/06_embed.py

Dependencies:
    pip install sentence-transformers chromadb tqdm
"""

import json
import os
import time
from datetime import datetime

import chromadb
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ============================================================
# Configuration
# ============================================================
CHUNKS_PATH      = "data/chunks/cruxbot_chunks.json"
OUTPUT_DIR       = "data/embeddings"
CHROMA_DIR       = "data/chroma"
EMBEDDED_PATH    = os.path.join(OUTPUT_DIR, "cruxbot_embedded.json")
CHECKPOINT_PATH  = os.path.join(OUTPUT_DIR, "checkpoint.json")

COLLECTION_NAME  = "cruxbot"
MODEL_NAME       = "all-MiniLM-L6-v2"   # swap here to try bge-base-en-v1.5

BATCH_SIZE        = 256    # chunks per encoding batch
CHROMA_BATCH_SIZE = 500    # chunks per ChromaDB upsert call
CHECKPOINT_EVERY  = 10     # save checkpoint every N encoding batches

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHROMA_DIR, exist_ok=True)


# ============================================================
# Metadata extraction — ChromaDB only stores flat string/int/float/bool
# ============================================================
CHROMA_META_FIELDS = [
    "content_type", "source", "source_url",
    "grade", "route_type", "location", "lat", "lng",
    "parent_doc_id", "chunk_index", "total_chunks",
]

def extract_chroma_metadata(chunk: dict) -> dict:
    """
    Extract flat metadata fields for ChromaDB.
    Nested dicts (like 'metadata') are flattened one level.
    All values coerced to str/int/float/bool.
    """
    meta = {}

    for field in CHROMA_META_FIELDS:
        val = chunk.get(field, "")
        if val is None:
            val = ""
        meta[field] = val

    # Flatten the nested 'metadata' dict
    for k, v in (chunk.get("metadata") or {}).items():
        if v is None:
            v = ""
        if isinstance(v, (str, int, float, bool)):
            meta[f"meta_{k}"] = v
        else:
            meta[f"meta_{k}"] = str(v)

    # Ensure no None values sneak through
    return {k: ("" if v is None else v) for k, v in meta.items()}


# ============================================================
# Checkpoint helpers
# ============================================================
def load_checkpoint() -> dict:
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, "r") as f:
            return json.load(f)
    return {"last_batch": -1, "embedded_chunk_ids": []}


def save_checkpoint(last_batch: int, embedded_ids: list[str]):
    with open(CHECKPOINT_PATH, "w") as f:
        json.dump({"last_batch": last_batch, "embedded_chunk_ids": embedded_ids}, f)


# ============================================================
# Main pipeline
# ============================================================
def main():
    print("=" * 60)
    print(" CruxBot Embedding Pipeline")
    print(f"   Model:  {MODEL_NAME}")
    print(f"   Input:  {CHUNKS_PATH}")
    print(f"   ChromaDB: {CHROMA_DIR}/{COLLECTION_NAME}")
    print(f"   Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load chunks
    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"  Loaded {len(chunks):,} chunks")

    # Resume from checkpoint
    checkpoint = load_checkpoint()
    resume_batch = checkpoint["last_batch"] + 1
    embedded_ids = set(checkpoint["embedded_chunk_ids"])

    if resume_batch > 0:
        print(f"\n Resuming from batch {resume_batch} ({len(embedded_ids):,} chunks already embedded)")
        chunks_to_embed = [c for c in chunks if c["chunk_id"] not in embedded_ids]
    else:
        chunks_to_embed = chunks

    print(f"  Chunks to embed: {len(chunks_to_embed):,}")

    # Load model
    print(f"\n Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print(f"  Embedding dim: {model.get_sentence_embedding_dimension()}")

    # Init ChromaDB
    print(f"\n  Connecting to ChromaDB ({CHROMA_DIR})")
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine similarity
    )
    print(f"  Collection '{COLLECTION_NAME}' ready ({collection.count():,} existing vectors)")

    # Load existing embedded backup (for appending)
    if os.path.exists(EMBEDDED_PATH) and resume_batch > 0:
        with open(EMBEDDED_PATH, "r", encoding="utf-8") as f:
            embedded_backup = json.load(f)
        print(f"  {len(embedded_backup):,} already saved")
    else:
        embedded_backup = []

    # Batch encode + upsert 
    print(f"\n Encoding and upserting ({BATCH_SIZE} chunks/batch)")

    batches = [
        chunks_to_embed[i : i + BATCH_SIZE]
        for i in range(0, len(chunks_to_embed), BATCH_SIZE)
    ]

    total_upserted = 0
    start_time = time.time()

    for batch_idx, batch in enumerate(tqdm(batches, desc="Batches", unit="batch")):
        texts = [c["text"] for c in batch]

        # Encode
        embeddings = model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,   # cosine sim = dot product after normalization
        )

        # Attach embeddings to backup list
        for chunk, emb in zip(batch, embeddings):
            chunk_with_emb = {**chunk, "embedding": emb.tolist()}
            embedded_backup.append(chunk_with_emb)
            embedded_ids.add(chunk["chunk_id"])

        # Upsert to ChromaDB in sub-batches
        for start in range(0, len(batch), CHROMA_BATCH_SIZE):
            sub_batch  = batch[start : start + CHROMA_BATCH_SIZE]
            sub_embs   = embeddings[start : start + CHROMA_BATCH_SIZE]

            collection.upsert(
                ids        = [c["chunk_id"] for c in sub_batch],
                embeddings = sub_embs.tolist(),
                documents  = [c["text"] for c in sub_batch],
                metadatas  = [extract_chroma_metadata(c) for c in sub_batch],
            )

        total_upserted += len(batch)

        # Checkpoint
        if (batch_idx + 1) % CHECKPOINT_EVERY == 0:
            save_checkpoint(resume_batch + batch_idx, list(embedded_ids))
            # Also flush backup to disk
            with open(EMBEDDED_PATH, "w", encoding="utf-8") as f:
                json.dump(embedded_backup, f, ensure_ascii=False, default=str)

    # Final save

    # JSON backup
    with open(EMBEDDED_PATH, "w", encoding="utf-8") as f:
        json.dump(embedded_backup, f, ensure_ascii=False, default=str)
    size_mb = os.path.getsize(EMBEDDED_PATH) / 1024 / 1024
    print(f"  Embedded backup: {EMBEDDED_PATH} ({len(embedded_backup):,} chunks, {size_mb:.1f} MB)")

    # Clear checkpoint on clean finish
    if os.path.exists(CHECKPOINT_PATH):
        os.remove(CHECKPOINT_PATH)
        print(f"  Checkpoint cleared (clean finish)")

    # Summary
    elapsed = time.time() - start_time
    final_count = collection.count()

    print(f"\n Summary:")
    print(f"  Chunks embedded this run: {total_upserted:,}")
    print(f"  Total vectors in ChromaDB: {final_count:,}")
    print(f"  Embedding dim: {model.get_sentence_embedding_dimension()}")
    print(f"  Time elapsed: {elapsed:.0f}s ({total_upserted / max(elapsed, 1):.0f} chunks/sec)")

if __name__ == "__main__":
    main()
