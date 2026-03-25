# CruxBot — Next Steps & Team Roadmap

## Current Status

Data pipeline is complete:
- 338,433 unified entries across 6 sources
- 100% citation URLs
- Unified schema ready for embedding

Remaining work: everything from chunking to deployment.

---

## RAG Architecture

```
User Query
    │
    ▼
[1] Embed Query
    sentence-transformers → 384-dim vector
    │
    ▼
[2] Retrieve Top-K Chunks
    ChromaDB semantic search → Top 5 most relevant passages
    each passage carries: chunk_text, source_url, title
    │
    ▼
[3] Build Prompt
    "Based ONLY on the following climbing information, answer the question.
     If the answer is not in the provided context, say you don't have data.

     [chunk 1] ...
     [chunk 2] ...
     [chunk 3] ...

     Question: {user_query}"
    │
    ▼
[4] LLM Generation
    Ollama (Llama 3 8B) running locally on GCP
    generates natural language answer from the provided context
    │
    ▼
[5] Return Answer + Citations
    app.py displays LLM answer + clickable source_url links
    links come from retrieval step, not from LLM
```

**Key design decision — hallucination prevention:**
The prompt explicitly instructs the LLM to answer *only* from retrieved context.
If no relevant data exists in the database, the system responds:
> *"I don't have data on this in my knowledge base."*

This directly satisfies the grading criterion: *"Do we have confidence that the LLM will not hallucinate?"*
It should be demonstrated explicitly during the live demo.

---

## Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| Vector embeddings | `sentence-transformers` (all-MiniLM-L6-v2) | Fast, lightweight, 384-dim |
| Vector database | ChromaDB | Simple local setup, persistent storage |
| LLM | Llama 3 8B via Ollama | Local inference, no API cost |
| Orchestration | LangChain | Connects retrieval → prompt → LLM |
| Frontend | Streamlit | Fast to build, good enough for demo |
| Deployment | Docker + GCP | Required for containerized submission |

---

## Task Breakdown

### Member A — Chunking & Embedding
**Files:** `src/chunking.py`, `src/embedding.py`

This member built the data pipeline and knows the schema best — responsible for turning the unified JSON into a searchable vector database.

**Problems to solve:**

1. **What goes into each chunk?**
   - Decide whether to use only the `text` field, or also prepend structured fields like `grade` and `location`
   - Recommended: prepend key fields so queries like "5.10 routes in Texas" match better
   ```
   "Title: Yankee Clipper | Grade: 5.10b | Location: Hueco Tanks, Texas
    Yankee Clipper is a 5.10b Sport route in Hueco Tanks..."
   ```

2. **How to split long documents?**
   - Route entries are short — keep as single chunk
   - Forum posts and AAC articles can be long — split at sentence boundaries, not mid-sentence
   - Add overlap between chunks (last sentence of chunk N becomes first sentence of chunk N+1) to avoid cutting critical context

3. **What metadata to store in ChromaDB?**
   - Each chunk needs: `source_url`, `title`, `doc_id`, `content_type`
   - Optional filters: `grade`, `location` — enables retrieval like "only look in routes"

4. **Batch efficiency on GCP**
   - 338k entries cannot be embedded one by one — use batch size 64–256
   - Run on GCP GPU instance, test timing early
   - Persist ChromaDB to disk (`./chroma_db/`) so it survives restarts

---

### Member B — Retrieval & RAG Pipeline
**Files:** `src/retrieval.py`, `src/rag_pipeline.py`

Core logic of the system. Connects the vector database to the LLM.

**Problems to solve:**

1. **Retrieval quality**
   - Embed user query → query ChromaDB → return Top-5 chunks
   - Decide how many results to retrieve (too few = missing context, too many = noisy prompt)
   - Optionally add metadata filtering (e.g. only search `content_type == "route"` for route questions)

2. **Prompt design**
   - Must instruct LLM to answer *only* from retrieved context
   - Must handle the "no data" case cleanly — LLM should say it doesn't know, not hallucinate
   - Example prompt structure:
   ```
   Based ONLY on the following climbing information, answer the question.
   If the answer is not found in the context, say "I don't have data on this."

   [chunk 1] ...
   [chunk 2] ...

   Question: {user_query}
   ```

3. **Connecting to Ollama**
   - Call Ollama's local API to run Llama 3 8B
   - Handle slow responses gracefully (LLM inference takes a few seconds)

4. **Return format**
   - Output must include both the answer text and the list of source URLs
   - Sources come from chunk metadata, not from the LLM

---

### Member C — Frontend & Deployment
**Files:** `app.py`, `Dockerfile`, `docker-compose.yml`

Responsible for both the Streamlit UI and getting the full system running on GCP.

**Problems to solve:**

**Frontend:**
1. Build a chat-style interface with a text input and submit button
2. Display LLM answer clearly
3. Display clickable source links below the answer:
   ```
   Sources:
   • Yankee Clipper          → https://mountainproject.com/...
   • Forum: Hueco Tanks      → https://mountainproject.com/...
   ```
4. Show a loading spinner while waiting for LLM response
5. Add a sidebar with 3–5 preset example queries for demo day

**Deployment:**
1. Write `Dockerfile` for the Streamlit app
2. Write `docker-compose.yml` to start Ollama + Streamlit together
3. Deploy on GCP, expose a public IP
4. Mount ChromaDB index as a volume (do not rebuild it inside the container)
5. Test end-to-end: public IP → query → answer with citations before demo day

---

### Member D — Evaluation & Writeup
**Files:** project writeup PDF, slide deck

Responsible for documenting the system and preparing the demo presentation.

**Problems to solve:**

1. **Systems diagram**
   - Required in the writeup — draw the full architecture from query to response
   - Must show: user → Streamlit → retrieval → ChromaDB → prompt → Ollama → answer + citations

2. **Evaluation**
   - Prepare 5–10 test queries covering different cases:
     - Query that matches data well → cited answer
     - Query for a route not in the database → clean "no data" response (demonstrates anti-hallucination)
     - Edge cases: vague queries, multi-part questions
   - Document expected vs. actual outputs as evidence

3. **Writeup sections**
   - Motivation: why climbing knowledge is fragmented and why RAG helps
   - Data sources and cleaning methodology
   - RAG system design and prompt strategy
   - Evaluation results
   - Contributions section (what each member did)

4. **Slide deck**
   - Link to master deck on slide 2
   - Elevator pitch under 3 minutes
   - Include live demo queries and the "no data" case

---

## Dependency Order

```
Member A (chunking + embedding)
    └──► Member B (retrieval + RAG pipeline)
              ├──► Member C (frontend + deployment)
              └──► Member D (evaluation + writeup)
```

**Member A is the critical path — everyone else is blocked until ChromaDB is built.**
Start the embedding job on GCP as soon as possible.

---

## Milestone Schedule

Internal demo target: **April 8** (5 days before official demo day on April 13)

| Deadline | Milestone | Owner |
|----------|-----------|-------|
| **Mar 27** | GCP environment ready, Ollama + Llama 3 running | C |
| **Mar 28** | Chunking logic done, small batch test (1,000 entries) | A |
| **Mar 31** | Full 338k entries embedded into ChromaDB | A |
| **Apr 2** | Retrieval + RAG Pipeline end-to-end working | B1, B2 |
| **Apr 4** | Streamlit frontend done + Docker + GCP public IP accessible | C |
| **Apr 6** | Integration testing, bug fixes, demo queries prepared | All |
| **Apr 7** | Writeup + slides complete, pitch rehearsed | D |
| **Apr 8** | Internal demo — full system sign-off ✅ | All |

---

## Demo Day Checklist

- [ ] Server live at a public IP before 4:00pm
- [ ] 3–5 preset example queries ready
- [ ] One query where route is NOT in database → shows clean "no data" response
- [ ] All source links are clickable and point to real pages
- [ ] Response latency under 15 seconds

---

## Risk Items

| Risk | Mitigation |
|------|-----------|
| Embedding 338k entries takes too long | Start on GCP GPU early; can subset to 100k for demo if needed |
| Ollama latency too high on GCP | Use Llama 3 8B (not larger); test response time before demo day |
| ChromaDB not fitting in container | Mount as external volume in docker-compose |
| GCP deployment issues on demo day | Test full deployment at least 2 days before presentation |
