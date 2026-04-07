# 🧗 CruxBot — Intelligent Climbing Assistant

A Retrieval-Augmented Generation (RAG) system that serves as an intelligent rock climbing assistant. CruxBot consolidates fragmented climbing knowledge into a unified retrieval system powered by a locally hosted LLM.

> **CS 6120 — Natural Language Processing, Northeastern University**

## Overview

Climbing knowledge is scattered across forums, wikis, and databases. CruxBot solves this by:

1. **Retrieving** relevant climbing information from a 338k+ document knowledge base using hybrid search (BM25 + dense vector retrieval)
2. **Generating** accurate, cited answers using a locally hosted Llama 3 8B
3. **Citing** every response with clickable links to the original source

## Data Sources

| Source | Content | Entries | Method |
|--------|---------|---------|--------|
| [OpenBeta](https://openbeta.io) | Routes, grades, GPS (47 US states) | 85,898 | GraphQL API |
| [Mountain Project](https://www.kaggle.com/datasets/pdegner/mountain-project-rotues-and-forums) (Kaggle) | Routes with descriptions & URLs | 116,700 | Kaggle download |
| MP Forums (Kaggle) | Training, gear, technique discussions | 99,173 | Kaggle download |
| [AAC Articles](https://www.kaggle.com/datasets/iantonopoulos/american-alpine-club-articles) (Kaggle) | Accident reports, expedition records | 27,828 | Kaggle download |
| Reddit | Community discussions (2024–2026) | 2,372 | Public JSON endpoints |
| Gear Reviews (Kaggle) | Equipment reviews & ratings | 6,462 | Kaggle download |
| **Total** | | **338,433** | |

All entries are cleaned, deduplicated, and normalized into a unified schema. 100% have clickable source URLs for citation. See [DATA_COLLECTION_METHODS.md](DATA_COLLECTION_METHODS.md) for full documentation.

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | Llama 3 8B via [Ollama](https://ollama.ai/) (local, no API calls) |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Vector DB | ChromaDB |
| Retrieval | Hybrid search (BM25 + dense cosine similarity + RRF fusion) |
| Frontend | Streamlit (streaming output, keyword highlighting) |
| Deployment | Docker on GCP (NVIDIA L4 GPU) |

## Key Features

- **Hybrid Search**: BM25 keyword matching + dense vector retrieval merged via Reciprocal Rank Fusion (RRF)
- **Query Intent Detection**: Automatically classifies queries as route/training/safety/gear and filters retrieval accordingly
- **Grade Normalization**: Cross-system grade conversion (YDS ↔ French, V-scale ↔ Font) for better retrieval
- **Anti-Hallucination**: Domain-check prompt design ensures out-of-domain questions are correctly refused
- **Streaming Output**: Token-by-token response display for reduced perceived latency
- **Source Highlighting**: Query keywords are highlighted in retrieved source snippets
- **URL Validation**: Generic forum URLs are flagged; specific URLs are displayed as clickable links

## Evaluation Results

50-query test suite across 5 categories (v1 → v3 comparison):

| Category | v1 (baseline) | v3 (final) |
|----------|--------------|------------|
| Route | 50% | **70%** |
| Training | 40% | **100%** |
| Safety | 80% | **100%** |
| Gear | 70% | **90%** |
| Anti-hallucination | 100% | **90%** |
| **Overall** | **68%** | **90%** |

Key improvements from hybrid search, intent detection, grade normalization, and prompt engineering.

## Project Structure

```
cruxbot/
├── data/                          # Data files (not in git, too large)
│   ├── openbeta/                  # OpenBeta route data
│   ├── kaggle_8a/                 # Kaggle datasets (routes + forums + AAC)
│   ├── reddit/                    # Reddit posts
│   ├── unified/                   # Cleaned & unified final data (338k)
│   ├── chroma/                    # ChromaDB vector store (382k vectors)
│   └── evaluation_results.json    # Latest evaluation results
├── scripts/                       # Data collection & deployment
│   ├── 01_openbeta_collect.py     # OpenBeta GraphQL API (BFS + UUID)
│   ├── 02_kaggle_8a_collect.py    # Kaggle MP routes & forums
│   ├── 02b_aac_collect.py         # AAC articles
│   ├── 03_reddit_collect.py       # Reddit (public JSON endpoints)
│   ├── 04_clean_and_unify.py      # Cleaning + schema unification
│   ├── evaluate.py                # 50-query automated evaluation
│   ├── fix_forum_urls.py          # URL validation & flagging
│   ├── setup_gcp.sh               # First-time GCP VM setup
│   ├── start_gcp.sh               # Start stopped VM
│   ├── update_gcp.sh              # Push code updates to VM
│   └── update_chroma.sh           # Update ChromaDB on VM
├── src/                           # Core RAG pipeline
│   ├── retrieval.py               # Hybrid search (BM25 + dense + RRF)
│   ├── rag_pipeline.py            # RAG orchestration + streaming
│   ├── chunking.py                # Text chunking (300-500 tokens)
│   └── embedding.py               # Vector embedding + ChromaDB indexing
├── tests/
│   └── test_rag.py                # End-to-end RAG test
├── app.py                         # FastAPI backend
├── streamlit_app.py               # Streamlit frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DATA_COLLECTION_METHODS.md
└── README.md
```

## Quick Start

### 1. Setup Environment

```bash
git clone https://github.com/zongyang078/CruxBot.git
cd CruxBot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Collect Data

```bash
python -u scripts/01_openbeta_collect.py
python -u scripts/02_kaggle_8a_collect.py
python -u scripts/02b_aac_collect.py
python -u scripts/03_reddit_collect.py
python -u scripts/04_clean_and_unify.py
```

### 3. Build Index

```bash
python -u src/chunking.py
python -u src/embedding.py
```

### 4. Run Application (Local)

```bash
# Start Ollama (separate terminal)
ollama serve
ollama pull llama3

# Start Streamlit
streamlit run streamlit_app.py
```

### 5. Docker Deployment

```bash
docker compose up --build
```

## Unified Data Schema

Every entry in the knowledge base follows this schema:

```json
{
  "doc_id": "f83c6348003e",
  "title": "Access Denied",
  "text": "Access Denied is a 5.10b/c Sport climbing route...",
  "content_type": "route",
  "source": "mountain_project",
  "source_url": "https://www.mountainproject.com/route/110149834/access-denied",
  "grade": "5.10b/c",
  "route_type": "Sport",
  "location": "El Mirador > El Potrero Chico > ...",
  "lat": "25.95044",
  "lng": "-100.47755",
  "metadata": { "avg_stars": "2.9", "pitches": "4" }
}
```

5 content types: `route` | `forum_discussion` | `article` | `gear_review` | `reddit_post`

## Deployment (GCP)

### Architecture

```
GCP VM (NVIDIA L4 GPU)
├── ollama (GPU, runs Llama 3 8B)      :11434
├── app (FastAPI)                      :8080  ← API
└── streamlit (frontend UI)            :8501  ← user access
```

### Scripts

| Script | When to use |
|--------|-------------|
| `bash scripts/setup_gcp.sh` | First-time setup — creates VM, installs drivers, uploads data, builds Docker |
| `bash scripts/start_gcp.sh` | Start stopped VM and bring up containers |
| `bash scripts/update_gcp.sh` | Push code updates, rebuild and restart containers |
| `bash scripts/update_chroma.sh <zip>` | Replace ChromaDB vector store |

> Note: First Streamlit request after restart triggers BM25 index build (~30s), cached automatically afterwards.

## Team

| Member | Contribution |
|--------|-------------|
| Sherwin Vahidimowlavi | Chunking pipeline, embedding pipeline, ChromaDB indexing (382k vectors) |
| Linxuan Li | Retrieval logic, RAG orchestration, Ollama integration, prompt design |
| Lingyun Xiao | Streamlit frontend, FastAPI backend, GCP deployment, Docker containerization |
| Zongyang Li | Data collection，hybrid search (BM25+dense+RRF), query intent detection, grade normalization, prompt engineering, anti-hallucination design, evaluation |
| All | Writeup |
## Team

| Member | Contribution |
|--------|-------------|
| Zongyang Li | Data collection (6 sources, 504k→338k), hybrid retrieval (BM25+dense+RRF), intent detection, grade normalization, prompt engineering, evaluation, writeup |
| Lingyun Xiao | GCP deployment, Docker containerization, Ollama/LLM infrastructure |
| Linxuan Li | Chunking pipeline, embedding pipeline, ChromaDB indexing |
| Sherwin Vahidimowlavi | Streamlit frontend, FastAPI backend |

## License

This project is for educational purposes (CS 6120 Final Project).
Data sources are used under their respective licenses: OpenBeta (CC0), AAC (CC0), Kaggle (copyright-authors), Reddit (API ToS).
