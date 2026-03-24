# 🧗 CruxBot — Intelligent Climbing Assistant

A Retrieval-Augmented Generation (RAG) system that serves as an intelligent rock climbing assistant. CruxBot consolidates fragmented climbing knowledge into a unified retrieval system powered by a locally hosted LLM.

> **CS 6120 — Natural Language Processing, Northeastern University**

## Overview

Climbing knowledge is scattered across forums, wikis, and databases. CruxBot solves this by:

1. **Retrieving** relevant climbing information from a 10k+ document knowledge base
2. **Generating** accurate, cited answers using a locally hosted LLM
3. **Citing** every response with clickable links to the original source

## Data Sources

| Source | Content | Volume |
|--------|---------|--------|
| [OpenBeta](https://openbeta.io) | Route names, grades, descriptions, GPS | ~5-8k routes |
| [8a.nu (Kaggle)](https://www.kaggle.com/dcohen21/8anu-climbing-logbook) | Ascent logs, user profiles, performance data | ~5k+ entries |
| [Reddit](https://www.reddit.com/r/climbing/) | Training, gear, technique discussions | ~3-5k posts |

## Tech Stack

- **LLM**: Llama 3 8B / Mistral 7B via [Ollama](https://ollama.ai/) (local)
- **Embeddings**: sentence-transformers (`all-MiniLM-L6-v2`)
- **Vector DB**: ChromaDB
- **Orchestration**: LangChain
- **Frontend**: Streamlit
- **Deployment**: Docker on GCP

## Project Structure

```
cruxbot/
├── data/                  # Raw and processed data (not in git)
│   ├── openbeta/
│   ├── kaggle_8a/
│   └── reddit/
├── scripts/               # Data collection scripts
│   ├── 01_openbeta_collect.py
│   ├── 02_kaggle_8a_collect.py
│   └── 03_reddit_collect.py
├── src/                   # Core RAG pipeline
│   ├── chunking.py
│   ├── embedding.py
│   ├── retrieval.py
│   └── rag_pipeline.py
├── app.py                 # Streamlit frontend
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Quick Start

### 1. Setup Environment

```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### 2. Collect Data

```bash
python scripts/01_openbeta_collect.py
python scripts/02_kaggle_8a_collect.py
python scripts/03_reddit_collect.py
```

### 3. Build Index

```bash
python src/embedding.py
```

### 4. Run Application

```bash
# Start Ollama (in a separate terminal)
ollama serve
ollama pull llama3

# Start Streamlit
streamlit run app.py
```

### 5. Docker (Production)

```bash
docker-compose up --build
```

## Team

| Member | Contribution |
|--------|-------------|
| TBD | TBD |

## License

This project is for educational purposes (CS 6120 Final Project).
Data sources are used under their respective licenses (OpenBeta: CC0, Reddit: API ToS).
