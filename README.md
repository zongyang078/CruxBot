# 🧗 CruxBot — Intelligent Climbing Assistant

A Retrieval-Augmented Generation (RAG) system that serves as an intelligent rock climbing assistant. CruxBot consolidates fragmented climbing knowledge into a unified retrieval system powered by a locally hosted LLM.

> **CS 6120 — Natural Language Processing, Northeastern University**

## Overview

Climbing knowledge is scattered across forums, wikis, and databases. CruxBot solves this by:

1. **Retrieving** relevant climbing information from a 338k+ document knowledge base
2. **Generating** accurate, cited answers using a locally hosted LLM
3. **Citing** every response with clickable links to the original source

## Data Sources

| Source                                                                                                  | Content                               | Entries     | Method                |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------- | ----------- | --------------------- |
| [OpenBeta](https://openbeta.io)                                                                         | Routes, grades, GPS (47 US states)    | 85,898      | GraphQL API           |
| [Mountain Project](https://www.kaggle.com/datasets/pdegner/mountain-project-rotues-and-forums) (Kaggle) | Routes with descriptions & URLs       | 116,700     | Kaggle download       |
| MP Forums (Kaggle)                                                                                      | Training, gear, technique discussions | 99,173      | Kaggle download       |
| [AAC Articles](https://www.kaggle.com/datasets/iantonopoulos/american-alpine-club-articles) (Kaggle)    | Accident reports, expedition records  | 27,828      | Kaggle download       |
| Reddit                                                                                                  | Community discussions (2024–2026)     | 2,372       | Public JSON endpoints |
| Gear Reviews (Kaggle)                                                                                   | Equipment reviews & ratings           | 6,462       | Kaggle download       |
| **Total**                                                                                               |                                       | **338,433** |                       |

All entries are cleaned, deduplicated, and normalized into a unified schema. 100% have clickable source URLs for citation. See [DATA_COLLECTION_METHODS.md](DATA_COLLECTION_METHODS.md) for full documentation.

## Tech Stack

- **LLM**: Llama 3 8B / Mistral 7B via [Ollama](https://ollama.ai/) (local, no API calls)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`, 384-dim)
- **Vector DB**: ChromaDB
- **Orchestration**: LangChain
- **Frontend**: Streamlit
- **Deployment**: Docker on GCP

## Project Structure

```
cruxbot/
├── data/                          # Data files (not in git, too large)
│   ├── openbeta/                  # OpenBeta route data (204k raw)
│   ├── kaggle_8a/                 # Kaggle datasets (routes + forums + AAC)
│   ├── reddit/                    # Reddit posts (2.5k)
│   └── unified/                   # Cleaned & unified final data (338k)
├── scripts/                       # Data collection & processing
│   ├── 01_openbeta_collect.py     # OpenBeta GraphQL API (BFS + UUID)
│   ├── 02_kaggle_8a_collect.py    # Kaggle MP routes & forums
│   ├── 02b_aac_collect.py         # AAC articles
│   ├── 03_reddit_collect.py       # Reddit (public JSON endpoints)
│   └── 04_clean_and_unify.py      # Cleaning + schema unification
├── src/                           # Core RAG pipeline
│   ├── chunking.py                # Text chunking (300-500 tokens)
│   ├── embedding.py               # Vector embedding
│   ├── retrieval.py               # Semantic search + metadata filtering
│   └── rag_pipeline.py            # End-to-end RAG orchestration
├── app.py                         # Streamlit frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── DATA_COLLECTION_METHODS.md     # Detailed data documentation
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

### 2. Collect Data (or get from Google Drive)

```bash
# OpenBeta routes (takes ~30 min, 204k routes)
python -u scripts/01_openbeta_collect.py

# Kaggle datasets (requires Kaggle API token)
export KAGGLE_API_TOKEN=your_token_here
python -u scripts/02_kaggle_8a_collect.py
python -u scripts/02b_aac_collect.py

# Reddit posts
python -u scripts/03_reddit_collect.py

# Clean and unify all data
python -u scripts/04_clean_and_unify.py
```

### 3. Build Index (TODO)

```bash
python src/embedding.py
```

### 4. Run Application (TODO)

```bash
# Start Ollama (separate terminal)
ollama serve
ollama pull llama3

# Start Streamlit
streamlit run app.py
```

### 5. Docker (TODO)

```bash
docker-compose up --build
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

## Project Status

- [x] Data collection (6 sources, 504k raw entries)
- [x] Data cleaning & deduplication (338k unified entries)
- [x] Unified schema with 100% citation URLs
- [ ] Chunking & embedding
- [ ] ChromaDB indexing
- [ ] LLM deployment (Ollama + Llama 3)
- [ ] RAG pipeline
- [ ] Streamlit frontend
- [ ] Docker containerization
- [ ] Evaluation & writeup

## Team

| Member | Contribution |
| ------ | ------------ |
| TBD    | TBD          |

## License

This project is for educational purposes (CS 6120 Final Project).
Data sources are used under their respective licenses: OpenBeta (CC0), AAC (CC0), Kaggle (copyright-authors), Reddit (API ToS).

GCP VM

1. VM — Compute Engine GPU T4，Ubuntu 22.04，firewall 8080/8501
2. install env — Docker + NVIDIA Container Toolkit
3. upload code & data
   gcloud compute scp --recurse ./CruxBot <VM name>:~/
4. pull llama3
   docker compose up -d ollama
   docker compose exec ollama ollama pull llama3
5. start service
   docker compose up -d

outside VM access：http://<VMIP>:8501

GCP VM
├── ollama (GPU，locally run llama3) :11434
├── app (FastAPI) :8080 ← API
└── streamlit (frontend UI) :8501 ← user access
