"""
CruxBot — Hybrid Retrieval Module (v3)
========================================
Combines dense vector search (ChromaDB) with sparse keyword search (BM25)
using Reciprocal Rank Fusion (RRF) for re-ranking.

Why hybrid?
  - Dense (embedding) is good at semantic matching:
    "How to get stronger fingers" → matches "hangboard training protocol"
  - Sparse (BM25) is good at exact keyword matching:
    "5.10a sport route Joshua Tree" → matches docs containing those exact words
  - Hybrid combines both strengths, dramatically reducing over-conservative refusals

Architecture:
  - BM25 index is built from ChromaDB documents at startup (one-time, ~10s)
  - At query time: dense top-K + BM25 top-K → RRF merge → final top-K
  - No additional infrastructure needed (no Elasticsearch)

Dependencies (add to requirements.txt):
  rank_bm25>=0.2.2

Usage:
  Drop-in replacement for retrieval.py — same function signature.
"""

import re
import json
import os
import pickle
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

# BM25 import — lightweight, pure Python, no external services
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False
    print("WARNING: rank_bm25 not installed. Falling back to dense-only retrieval.")
    print("  Install with: pip install rank_bm25")

# ============================================================
# Singletons
# ============================================================
_model = None
_collection = None
_bm25_index = None
_bm25_corpus_ids = None    # chunk_id list aligned with BM25 index
_bm25_corpus_meta = None   # metadata list aligned with BM25 index
_bm25_corpus_docs = None   # document text list aligned with BM25 index

BM25_CACHE_PATH = "data/bm25_cache.pkl"


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _get_collection(chroma_path: str = "data/chroma", collection_name: str = "cruxbot"):
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path=chroma_path)
        _collection = client.get_collection(collection_name)
    return _collection


# ============================================================
# BM25 Index Builder
# ============================================================

def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer for BM25."""
    text = text.lower()
    # Keep alphanumeric, dots (for grades like 5.10a), and hyphens
    tokens = re.findall(r"[a-z0-9]+(?:\.[a-z0-9]+)*(?:-[a-z0-9]+)*", text)
    return tokens


def _build_bm25_index(chroma_path: str = "data/chroma", collection_name: str = "cruxbot"):
    """
    Build a BM25 index from all documents in ChromaDB.
    Caches the index to disk so subsequent startups are fast.
    """
    global _bm25_index, _bm25_corpus_ids, _bm25_corpus_meta, _bm25_corpus_docs

    # Try loading from cache
    if os.path.exists(BM25_CACHE_PATH):
        try:
            with open(BM25_CACHE_PATH, "rb") as f:
                cache = pickle.load(f)
            _bm25_index = cache["index"]
            _bm25_corpus_ids = cache["ids"]
            _bm25_corpus_meta = cache["meta"]
            _bm25_corpus_docs = cache["docs"]
            print(f"  BM25 index loaded from cache ({len(_bm25_corpus_ids):,} docs)")
            return
        except Exception as e:
            print(f"  BM25 cache load failed ({e}), rebuilding...")

    print("  Building BM25 index from ChromaDB (one-time, may take ~30s)...")
    collection = _get_collection(chroma_path, collection_name)
    total = collection.count()

    all_ids = []
    all_docs = []
    all_meta = []
    batch_size = 5000
    offset = 0

    while offset < total:
        batch = collection.get(
            limit=batch_size,
            offset=offset,
            include=["documents", "metadatas"],
        )
        all_ids.extend(batch["ids"])
        all_docs.extend(batch["documents"])
        all_meta.extend(batch["metadatas"])
        offset += batch_size
        print(f"    Loaded {min(offset, total):,}/{total:,}", end="\r")

    print(f"\n  Tokenizing {len(all_docs):,} documents...")
    tokenized = [_tokenize(doc) for doc in all_docs]

    print("  Fitting BM25...")
    _bm25_index = BM25Okapi(tokenized)
    _bm25_corpus_ids = all_ids
    _bm25_corpus_meta = all_meta
    _bm25_corpus_docs = all_docs

    # Cache to disk
    try:
        cache = {
            "index": _bm25_index,
            "ids": _bm25_corpus_ids,
            "meta": _bm25_corpus_meta,
            "docs": _bm25_corpus_docs,
        }
        with open(BM25_CACHE_PATH, "wb") as f:
            pickle.dump(cache, f)
        size_mb = os.path.getsize(BM25_CACHE_PATH) / 1024 / 1024
        print(f"  BM25 index cached to {BM25_CACHE_PATH} ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  Warning: could not cache BM25 index: {e}")

    print(f"  BM25 index ready ({len(all_ids):,} documents)")


def _get_bm25(chroma_path: str = "data/chroma"):
    """Lazy-init BM25 index."""
    global _bm25_index
    if _bm25_index is None:
        _build_bm25_index(chroma_path)
    return _bm25_index


# ============================================================
# Grade Normalization (same as v2)
# ============================================================

_YDS_TO_FRENCH = {
    "5.5": "4a", "5.6": "4b", "5.7": "4c", "5.8": "5a", "5.9": "5b",
    "5.10a": "6a", "5.10b": "6a+", "5.10c": "6b", "5.10d": "6b+",
    "5.11a": "6c", "5.11b": "6c+", "5.11c": "7a", "5.11d": "7a+",
    "5.12a": "7a+", "5.12b": "7b", "5.12c": "7b+", "5.12d": "7c",
    "5.13a": "7c+", "5.13b": "8a", "5.13c": "8a+", "5.13d": "8b",
    "5.14a": "8b+", "5.14b": "8c", "5.14c": "8c+", "5.14d": "9a",
}
_FRENCH_TO_YDS = {v: k for k, v in _YDS_TO_FRENCH.items()}

_V_TO_FONT = {
    "V0": "4", "V1": "5", "V2": "5+", "V3": "6A", "V4": "6B",
    "V5": "6C", "V6": "7A", "V7": "7A+", "V8": "7B+", "V9": "7C",
    "V10": "7C+", "V11": "8A", "V12": "8A+", "V13": "8B", "V14": "8B+",
    "V15": "8C", "V16": "8C+",
}


def get_grade_equivalents(grade: str) -> list[str]:
    grade = grade.strip()
    equivalents = {grade}
    if re.match(r"^5\.\d+", grade):
        base = re.match(r"^(5\.\d+)", grade).group(1)
        equivalents.add(base)
        french = _YDS_TO_FRENCH.get(grade)
        if french:
            equivalents.add(french)
        if grade == base and int(base.split(".")[1]) >= 10:
            for suffix in ["a", "b", "c", "d"]:
                equivalents.add(f"{base}{suffix}")
                french = _YDS_TO_FRENCH.get(f"{base}{suffix}")
                if french:
                    equivalents.add(french)
    elif re.match(r"^[4-9][a-c]\+?$", grade, re.IGNORECASE):
        yds = _FRENCH_TO_YDS.get(grade)
        if yds:
            equivalents.add(yds)
            base = re.match(r"^(5\.\d+)", yds).group(1)
            equivalents.add(base)
    elif re.match(r"^V\d+", grade, re.IGNORECASE):
        font = _V_TO_FONT.get(grade.upper())
        if font:
            equivalents.add(font)
    return list(equivalents)


def extract_grade_from_query(query: str) -> str | None:
    m = re.search(r"\b(5\.\d{1,2}[a-d]?)\b", query, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\b(V\d{1,2})\b", query, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r"\b([4-9][a-c]\+?)\b", query, re.IGNORECASE)
    if m:
        return m.group(1)
    return None


# ============================================================
# Query Intent Detection (same as v2)
# ============================================================

_INTENT_PATTERNS = {
    "route": [
        r"\broute\b", r"\bclimb\b", r"\bcrag\b", r"\bwall\b", r"\bpitch\b",
        r"\bmulti-pitch\b", r"\bboulder(?:ing)?\b", r"\btrad\b", r"\bsport\b",
        r"\barea\b", r"\bclassic\b",
        r"\byosemite\b", r"\bjoshua tree\b", r"\bred river gorge\b",
        r"\bbishop\b", r"\bsmith rock\b", r"\bel potrero\b",
        r"\brumney\b", r"\bnew river gorge\b", r"\bindian creek\b",
        r"\bhueco\b", r"\butah\b", r"\bcolorado\b", r"\bcalifornia\b",
    ],
    "forum_discussion": [
        r"\btrain(?:ing)?\b", r"\bworkout\b", r"\bhangboard\b", r"\bcampus\b",
        r"\bfootwork\b", r"\btechnique\b", r"\bendurance\b", r"\bstrength\b",
        r"\bplateau\b", r"\bflexib(?:le|ility)\b", r"\bstretch\b",
        r"\binjur(?:y|ies)\b", r"\bpreven(?:t|tion)\b", r"\brecov(?:er|ery)\b",
        r"\btips?\b", r"\badvice\b", r"\bhow (?:do|should|can|to)\b",
    ],
    "article": [
        r"\baccident\b", r"\bfatal(?:ity)?\b", r"\bdeath\b", r"\bfall\b",
        r"\bsafety\b", r"\brescue\b", r"\brappel\b", r"\bbelay(?:ing)?\b",
        r"\banchor\b", r"\bprotection\b", r"\brockfall\b", r"\bknot\b",
        r"\bfree solo\b", r"\brisk\b", r"\bdanger\b",
    ],
    "gear_review": [
        r"\bgear\b", r"\bequipment\b", r"\bshoe\b", r"\bharness\b",
        r"\bhelmet\b", r"\brope\b", r"\bcarabiner\b", r"\bquickdraw\b",
        r"\bbelay device\b", r"\batc\b", r"\bgrigri\b", r"\bcrash pad\b",
        r"\bchalk\b", r"\bcam\b", r"\bnut\b", r"\breview\b", r"\bbuy\b",
        r"\brecommend\b", r"\bbest\b.*\bfor\b", r"\bcompari?son\b",
        r"\bla sportiva\b", r"\bscarpa\b", r"\bblack diamond\b", r"\bpetzl\b",
    ],
}


def detect_query_intent(query: str) -> str | None:
    query_lower = query.lower()
    scores = {}
    for content_type, patterns in _INTENT_PATTERNS.items():
        score = sum(1 for p in patterns if re.search(p, query_lower))
        if score > 0:
            scores[content_type] = score
    if not scores:
        return None
    sorted_scores = sorted(scores.items(), key=lambda x: -x[1])
    best_type, best_score = sorted_scores[0]
    if len(sorted_scores) == 1 and best_score >= 1:
        return best_type
    if len(sorted_scores) >= 2:
        second_score = sorted_scores[1][1]
        if best_score >= 2 * second_score:
            return best_type
    return None


# ============================================================
# Source URL Validation (same as v2)
# ============================================================

_GENERIC_URLS = {
    "https://www.mountainproject.com/forum",
    "https://www.mountainproject.com",
    "https://www.reddit.com",
    "https://openbeta.io",
}


def is_specific_url(url: str) -> bool:
    if not url:
        return False
    return url.strip().rstrip("/") not in _GENERIC_URLS


# ============================================================
# Reciprocal Rank Fusion (RRF)
# ============================================================

def _rrf_merge(
    dense_results: list[dict],
    bm25_results: list[dict],
    k: int = 60,
    dense_weight: float = 1.0,
    bm25_weight: float = 1.0,
) -> list[dict]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    RRF score = sum( weight / (k + rank) ) across lists where the doc appears.
    k=60 is the standard constant from the original RRF paper (Cormack et al. 2009).

    Higher dense_weight favors semantic matches.
    Higher bm25_weight favors keyword matches.
    """
    scores = {}  # chunk_id → {"score": float, "chunk": dict}

    for rank, chunk in enumerate(dense_results):
        cid = chunk.get("chunk_id") or chunk["text"][:50]  # fallback key
        rrf_score = dense_weight / (k + rank)
        if cid not in scores:
            scores[cid] = {"score": 0.0, "chunk": chunk}
        scores[cid]["score"] += rrf_score

    for rank, chunk in enumerate(bm25_results):
        cid = chunk.get("chunk_id") or chunk["text"][:50]
        rrf_score = bm25_weight / (k + rank)
        if cid not in scores:
            scores[cid] = {"score": 0.0, "chunk": chunk}
        scores[cid]["score"] += rrf_score

    # Sort by combined RRF score (descending)
    merged = sorted(scores.values(), key=lambda x: -x["score"])
    return [item["chunk"] for item in merged]


# ============================================================
# BM25 Retrieval
# ============================================================

def _bm25_retrieve(
    query: str,
    top_k: int = 20,
    chroma_path: str = "data/chroma",
    content_type_filter: str | None = None,
) -> list[dict]:
    """Retrieve top-k chunks using BM25 keyword matching."""
    if not HAS_BM25:
        return []

    bm25 = _get_bm25(chroma_path)
    tokens = _tokenize(query)
    if not tokens:
        return []

    # BM25 scores for all documents
    scores = bm25.get_scores(tokens)

    # Build (score, index) pairs, optionally filtered by content_type
    candidates = []
    for idx, score in enumerate(scores):
        if score <= 0:
            continue
        if content_type_filter:
            meta = _bm25_corpus_meta[idx]
            ct = meta.get("content_type", "")
            # Support $in-style filtering
            if isinstance(content_type_filter, str):
                if ct != content_type_filter:
                    continue
            elif isinstance(content_type_filter, list):
                if ct not in content_type_filter:
                    continue
        candidates.append((score, idx))

    # Sort by BM25 score descending, take top_k
    candidates.sort(key=lambda x: -x[0])
    top = candidates[:top_k]

    chunks = []
    for score, idx in top:
        meta = _bm25_corpus_meta[idx]
        source_url = meta.get("source_url", "")
        chunks.append({
            "text": _bm25_corpus_docs[idx],
            "chunk_id": _bm25_corpus_ids[idx],
            "source_url": source_url,
            "source_url_specific": is_specific_url(source_url),
            "score": score,
            "metadata": meta,
        })

    return chunks


# ============================================================
# Dense Retrieval (same as v2 but returns chunk_id)
# ============================================================

def _dense_retrieve(
    query: str,
    top_k: int = 20,
    chroma_path: str = "data/chroma",
    where_filter: dict | None = None,
) -> list[dict]:
    """Retrieve top-k chunks using dense vector search."""
    model = _get_model()
    collection = _get_collection(chroma_path)

    # Grade expansion
    grade = extract_grade_from_query(query)
    expanded_query = query
    if grade:
        equivalents = get_grade_equivalents(grade)
        extras = [g for g in equivalents if g.lower() not in query.lower()]
        if extras:
            expanded_query = f"{query} (grades: {', '.join(extras)})"

    query_embedding = model.encode(expanded_query).tolist()

    query_kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where_filter:
        query_kwargs["where"] = where_filter

    try:
        results = collection.query(**query_kwargs)
    except Exception:
        # If filter causes error, retry without
        query_kwargs.pop("where", None)
        results = collection.query(**query_kwargs)

    chunks = []
    for chunk_id, doc, meta, dist in zip(
        results["ids"][0],
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        source_url = meta.get("source_url", "")
        chunks.append({
            "text": doc,
            "chunk_id": chunk_id,
            "source_url": source_url,
            "source_url_specific": is_specific_url(source_url),
            "score": dist,
            "metadata": meta,
        })

    return chunks


# ============================================================
# Main Retrieve Function — Hybrid Search
# ============================================================

def retrieve(
    query: str,
    top_k: int = 5,
    chroma_path: str = "data/chroma",
    content_type_filter: str | None = None,
    use_intent_detection: bool = True,
    use_hybrid: bool = True,
    dense_weight: float = 1.0,
    bm25_weight: float = 1.0,
) -> list[dict]:
    """
    Hybrid retrieval: Dense (ChromaDB) + Sparse (BM25) merged via RRF.

    When use_hybrid=True (default):
      1. Dense retrieval → top 20 candidates
      2. BM25 retrieval  → top 20 candidates
      3. RRF merge       → final top_k results

    When use_hybrid=False:
      Falls back to dense-only retrieval (v2 behavior).

    Args:
        query: User's question
        top_k: Number of final results to return
        chroma_path: Path to ChromaDB persistent storage
        content_type_filter: Force a specific content type (overrides intent detection)
        use_intent_detection: Auto-detect content type from query keywords
        use_hybrid: Enable BM25 + dense hybrid search
        dense_weight: Weight for dense results in RRF (default 1.0)
        bm25_weight: Weight for BM25 results in RRF (default 1.0)
    """
    # --- Determine content type filter ---
    ct_filter_str = None   # for BM25 (string or list)
    where_filter = None    # for ChromaDB (dict)

    if content_type_filter:
        ct_filter_str = content_type_filter
        where_filter = {"content_type": content_type_filter}
    elif use_intent_detection:
        detected = detect_query_intent(query)
        if detected:
            if detected == "forum_discussion":
                ct_filter_str = ["forum_discussion", "reddit_post"]
                where_filter = {"content_type": {"$in": ["forum_discussion", "reddit_post"]}}
            elif detected == "gear_review":
                ct_filter_str = ["gear_review", "forum_discussion"]
                where_filter = {"content_type": {"$in": ["gear_review", "forum_discussion"]}}
            elif detected == "article":
                ct_filter_str = ["article", "forum_discussion"]
                where_filter = {"content_type": {"$in": ["article", "forum_discussion"]}}
            else:
                ct_filter_str = detected
                where_filter = {"content_type": detected}

    # --- Retrieve candidates ---
    # Fetch more candidates than top_k so RRF has enough to work with
    candidate_k = max(top_k * 4, 20)

    dense_results = _dense_retrieve(
        query, top_k=candidate_k, chroma_path=chroma_path, where_filter=where_filter
    )

    if use_hybrid and HAS_BM25:
        bm25_results = _bm25_retrieve(
            query, top_k=candidate_k, chroma_path=chroma_path,
            content_type_filter=ct_filter_str
        )
        merged = _rrf_merge(dense_results, bm25_results,
                            dense_weight=dense_weight, bm25_weight=bm25_weight)
    else:
        merged = dense_results

    # --- Take final top_k ---
    final = merged[:top_k]

    # --- Fallback: if filtered results are sparse, add unfiltered ---
    if where_filter and len(final) < top_k:
        unfiltered_dense = _dense_retrieve(query, top_k=top_k, chroma_path=chroma_path)
        seen_ids = {c.get("chunk_id") for c in final}
        for c in unfiltered_dense:
            if c.get("chunk_id") not in seen_ids and len(final) < top_k:
                final.append(c)
                seen_ids.add(c.get("chunk_id"))

    return final
