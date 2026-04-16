# CruxBot: An Intelligent Climbing Assistant via Retrieval-Augmented Generation

**CS 6120 — Natural Language Processing, Northeastern University**

**Team:** Sherwin Vahidimowlavi, Linxuan Li, Lingyun Xiao, Zongyang Li

---

## 1. Motivation and Impact

Rock climbing has undergone a surge in mainstream popularity, yet the knowledge infrastructure supporting the sport remains deeply fragmented. A climber seeking beta (route-specific information) for a trip to Yosemite must cross-reference Mountain Project for route descriptions, Reddit for recent conditions, American Alpine Club (AAC) journals for safety precedents, and gear forums for equipment recommendations — none of which communicate with one another. This fragmentation wastes time and, in safety-critical situations, can lead to poor decisions.

Existing solutions are inadequate. General-purpose search engines return documents but cannot synthesize answers. Conversational AI systems such as ChatGPT can synthesize, but they hallucinate route details, invent grades, and cite non-existent sources — a significant problem in a domain where incorrect information (e.g., wrong anchor setup, overstated grade) carries physical risk. Mountain Project's native search is keyword-based and silo'd to a single platform.

CruxBot addresses this gap by combining the structured knowledge of 338,433 curated climbing documents across six sources with a Retrieval-Augmented Generation (RAG) pipeline backed by a locally hosted Llama 3 8B. The system retrieves grounded context before generating any response, ensuring that every claim is traceable to a cited source.

**Future impact:** A productionized version of CruxBot could serve as the knowledge backbone for any outdoor sports community platform. The architecture generalizes to ice climbing, alpine mountaineering, trail running, or backcountry skiing with only data source changes. Integration with route planning apps or a mobile interface could bring expert-level safety guidance to climbers who currently make decisions with incomplete information.

---

## 2. Background and Related Work

### 2.1 Retrieval-Augmented Generation

RAG was introduced by Lewis et al. (2020) as a framework to augment language model generation with non-parametric knowledge retrieval. Rather than relying solely on weights trained at a fixed point in time, a RAG system retrieves relevant documents at inference time and conditions the generator on that retrieved context. This directly addresses the hallucination problem endemic to closed-book language models, and provides the citations necessary for a safety-conscious domain like climbing.

### 2.2 Dense and Sparse Retrieval

Our retrieval pipeline employs both sparse and dense retrieval, merged via Reciprocal Rank Fusion (RRF).

**BM25** (Robertson et al., 1994) is a bag-of-words ranking function that scores documents by term frequency and inverse document frequency. It excels at exact keyword matching — critical for climbing queries like route names ("Moonlight Buttress") or grades ("5.12d").

**Dense retrieval** (Karpukhin et al., 2020 — Dense Passage Retrieval) encodes both queries and documents into a shared vector space using a bi-encoder. We use `sentence-transformers/all-MiniLM-L6-v2` (Wang et al., 2020), a 384-dimensional model optimized for semantic similarity at low computational cost. Dense retrieval captures semantic equivalence that BM25 misses — e.g., "beginner-friendly" matching "easy warmup routes."

**Reciprocal Rank Fusion** (Cormack et al., 2009) merges ranked lists from BM25 and dense retrieval by combining their rank positions rather than raw scores, avoiding score normalization issues across heterogeneous ranking systems.

### 2.3 Language Model and Deployment

We use **Llama 3 8B** served locally via **Ollama**, a framework for running LLMs on commodity hardware. The choice to run locally (rather than via the OpenAI or Anthropic API) was motivated by two factors: (1) privacy — user queries are not sent to third parties, and (2) cost — zero per-query inference cost at scale. The trade-off is higher infrastructure complexity (GCP VM with NVIDIA L4 GPU).

**ChromaDB** serves as our vector store. It supports persistent disk-backed storage, metadata filtering, and batched upserts — sufficient for our 382,000-vector index without requiring a managed vector database service.

### 2.4 Related Systems

| System                  | Approach                      | Limitation vs. CruxBot                              |
| ----------------------- | ----------------------------- | --------------------------------------------------- |
| Mountain Project search | Keyword search, single source | No semantic understanding, no synthesis             |
| ChatGPT (GPT-4)         | Closed-book generation        | Hallucination, no climbing-specific citations       |
| Perplexity AI           | Web search + generation       | Not domain-specialized, no structured climbing data |
| CruxBot                 | Hybrid RAG, 6 curated sources | Domain-specific, cited, anti-hallucination          |

---

## 3. Modeling Methodology

### 3.1 System Architecture

```
User Query
    │
    ▼
[Query Intent Detection]
    Classify: route / training / safety / gear / other
    │
    ├──► Grade Normalization (route queries)
    │    Convert YDS ↔ French, V-scale ↔ Font
    │
    ▼
[Hybrid Retrieval]
    ├── BM25 (sparse keyword search) → ranked list A
    └── Dense (all-MiniLM-L6-v2 + ChromaDB cosine) → ranked list B
                        │
                        ▼
              Reciprocal Rank Fusion (RRF)
                        │
                        ▼
              Top-5 chunks (with source_url, title)
    │
    ▼
[Prompt Construction]
    System: "Answer ONLY from context. Refuse if out-of-domain."
    Context: [chunk 1] ... [chunk 2] ... [chunk 5]
    Query: {user_query}
    │
    ▼
[Llama 3 8B via Ollama — streaming]
    │
    ▼
Answer + Clickable Citations (Streamlit frontend)
```

### 3.2 Data Pipeline and Class Imbalance

The 338,433-entry knowledge base spans five content types with a highly skewed distribution:

| Content Type     | Entries | Fraction |
| ---------------- | ------- | -------- |
| route            | 202,598 | 59.9%    |
| forum_discussion | 99,173  | 29.3%    |
| article          | 27,828  | 8.2%     |
| gear_review      | 6,462   | 1.9%     |
| reddit_post      | 2,372   | 0.7%     |

Without intervention, a naive retriever would return predominantly route entries for most queries, even for questions best answered by forum discussions or safety articles. We address this in two ways:

**Query intent detection:** Queries are classified into one of five categories (route, training, safety, gear, general) using a rule-based classifier over query keywords. The retriever applies a soft content-type boost based on intent — e.g., a "safety" query upweights retrieval from `article` (AAC accident reports) and `forum_discussion` entries.

**Hybrid search as implicit rebalancing:** BM25 scores favor exact term matches, which are more likely in specialized content types (e.g., gear brand names in `gear_review`, route names in `route`). Combining BM25 and dense retrieval via RRF naturally surfaces content-type-diverse results rather than converging on the majority class.

### 3.3 Overfitting and Hallucination Prevention

Since CruxBot is a retrieval-and-generation system rather than a classifier trained on labeled data, "overfitting" manifests as the LLM over-relying on its pre-trained parametric knowledge rather than the retrieved context — i.e., hallucination.

We mitigate this with three prompt engineering techniques:

1. **Context-grounding instruction:** The system prompt explicitly instructs the LLM: _"Answer ONLY based on the following climbing information. Do not use any knowledge from your training. If the answer is not in the provided context, say 'I don't have data on this in my knowledge base.'"_

2. **Domain check:** The pipeline includes a domain classifier that detects queries unrelated to climbing (e.g., "write me a Python sorting algorithm"). These are rejected before retrieval, preventing the LLM from generating plausible-but-fabricated climbing answers to edge-case inputs.

3. **Source grounding:** Citations are extracted from chunk metadata at retrieval time, not generated by the LLM. This prevents the model from inventing URLs — a common failure mode in citation-generating systems.

### 3.4 Chunking Strategy

Long documents (AAC articles, forum threads) are split into 300–500 token chunks with a 50-token overlap between consecutive chunks, using sentence-boundary detection to prevent splitting mid-sentence. Short documents (routes, gear reviews) are kept as single chunks. Each chunk inherits the metadata of its parent document (`source_url`, `title`, `doc_id`, `content_type`).

### 3.5 Grade Normalization

Climbing grades use incompatible systems across countries and disciplines. A query for "7a routes" (French sport) should match documents graded "5.11d" (YDS) — the equivalent in the American system. We implement bidirectional conversion tables for YDS ↔ French, V-scale ↔ Fontainebleau, and YDS ↔ UIAA, expanding route queries to include grade equivalents before BM25 search.

---

## 4. Evaluation and Analysis

### 4.1 Evaluation Methodology

We designed a 50-query evaluation suite across five categories, covering the primary use cases of the system. Our evaluation uses a **two-tier approach**: binary pass/fail for version comparison, and LLM-as-Judge for nuanced quality scoring, validated by human evaluation on a representative subset.

**Why LLM-as-Judge instead of human evaluation alone.** Our original proposal specified a 1–5 Likert-scale human evaluation. However, LLM-as-Judge (Zheng et al., 2023) has become the standard evaluation methodology for RAG systems due to several practical advantages: it is scalable to hundreds of queries without annotator fatigue, produces consistent scores under a fixed rubric, and avoids inter-annotator disagreement that would require multiple raters and agreement metrics. Human evaluators may also lack the climbing domain expertise needed to reliably judge factual accuracy. We therefore use GPT-4o as our primary judge, with human evaluation on 10 representative queries (2 per category) to validate alignment between automated and human scores.

**Binary pass/fail rubric:**
- **Pass:** The answer is factually accurate relative to retrieved context, stays grounded (no fabrications), and correctly refuses out-of-domain queries (for anti-hallucination tests).
- **Fail:** The answer is wrong, hallucinated, misses relevant data present in the knowledge base, or answers an out-of-domain query.

We compared three system versions:

| Version       | Key Changes                                                                |
| ------------- | -------------------------------------------------------------------------- |
| v1 (baseline) | Dense-only retrieval, no intent detection, basic prompt                    |
| v2            | Added BM25 + RRF hybrid search, grade normalization                        |
| v3 (final)    | Added intent detection, domain-check anti-hallucination, prompt refinement |

### 4.2 Binary Pass/Fail Results (v1 → v3)

We first compared three system versions using a binary pass/fail rubric across 50 manually designed test queries:

| Version       | Key Changes                                                                |
| ------------- | -------------------------------------------------------------------------- |
| v1 (baseline) | Dense-only retrieval, no intent detection, basic prompt                    |
| v2            | Added BM25 + RRF hybrid search, grade normalization                        |
| v3 (final)    | Added intent detection, domain-check anti-hallucination, prompt refinement |

| Category           | v1 (baseline) | v3 (final) | Δ        |
| ------------------ | ------------- | ---------- | -------- |
| Route queries      | 50%           | **70%**    | +20%     |
| Training queries   | 40%           | **100%**   | +60%     |
| Safety queries     | 80%           | **100%**   | +20%     |
| Gear queries       | 70%           | **90%**    | +20%     |
| Anti-hallucination | 100%          | **90%**    | −10%     |
| **Overall**        | **68%**       | **90%**    | **+22%** |

### 4.3 LLM-as-Judge Evaluation (GPT-4o)

To complement the binary pass/fail evaluation with a more nuanced quality assessment, we implemented an **LLM-as-Judge** framework using GPT-4o as an automated evaluator. This approach is consistent with recent evaluation methodology (Zheng et al., 2023 — MT-Bench) and addresses the proposal's requirement for a Likert-scale quality assessment without requiring multiple human annotators.

**Rubric design.** GPT-4o was prompted with a structured rubric scoring each response on four dimensions:

| Dimension                  | Description                                                          |
| -------------------------- | -------------------------------------------------------------------- |
| **Relevance** (1–5)        | Does the answer directly address the user's query?                   |
| **Factual Accuracy** (1–5) | Are claims consistent with retrieved sources? No fabricated details? |
| **Citation Quality** (1–5) | Are source URLs specific and clickable, or generic placeholders?     |
| **Completeness** (1–5)     | Does the answer fully address the question given available sources?  |

For anti-hallucination queries (out-of-domain questions), the rubric instructs GPT-4o to award 5/5 across all dimensions for a correct refusal, and 1/5 for any response that answers instead of refusing. The judge receives the full query, CruxBot's complete answer, and the retrieved source metadata — it does not have access to ground truth labels.

**Results.** We ran GPT-4o evaluation on all 50 test queries (the same suite used for binary evaluation). Overall averages across all categories:

| Dimension        | Score           |
| ---------------- | --------------- |
| Relevance        | **4.40 / 5.00** |
| Completeness     | **3.74 / 5.00** |
| Factual Accuracy | **3.72 / 5.00** |
| Citation Quality | **2.78 / 5.00** |
| **Overall**      | **3.58 / 5.00** |

Results broken down by category:

| Category           | Relevance | Accuracy | Citation | Completeness | Overall  |
| ------------------ | --------- | -------- | -------- | ------------ | -------- |
| Anti-Hallucination | 4.60      | 4.60     | 4.60     | 4.60         | **4.60** |
| Safety             | 4.70      | 4.00     | 2.50     | 3.60         | **3.60** |
| Route              | 4.10      | 3.90     | 3.50     | 3.30         | **3.50** |
| Gear               | 4.40      | 3.00     | 1.80     | 3.60         | **3.10** |
| Training           | 4.20      | 3.10     | 1.50     | 3.60         | **3.10** |

> **Note on Citation Quality:** Since some data sources do not include specific post-level URLs in their metadata (e.g., Mountain Project forum posts from Kaggle), Citation Quality scores are lower for training and gear categories — this reflects a data limitation rather than a retrieval failure.

### 4.4 Analysis by Category

**Route (pass rate 70%, overall 3.5/5):** Relevance is high (4.1), indicating the system retrieves topically correct content. The lower completeness score (3.3) reflects that many route queries ask for specific beta (crux moves, approach time) that is absent from the retrieved chunks even when the route exists in the database. Hybrid search with grade normalization significantly improved recall over v1.

**Training (pass rate 100%, overall 3.1/5):** The most dramatic binary improvement (+60%) is confirmed by the LLM judge: relevance is strong (4.2), but citation quality is the lowest of all categories (1.5). This is a known data limitation — Mountain Project forum posts (the primary source for training advice) were collected from a Kaggle dataset that did not preserve individual post URLs, forcing all 99,173 forum entries to share a single generic URL (`mountainproject.com/forum`). GPT-4o correctly penalizes this.

**Safety (pass rate 100%, overall 3.6/5):** The best-performing content category. AAC accident report articles are long-form, factually dense, and carry specific `publications.americanalpineclub.org` URLs — explaining the relatively high citation score (2.5) compared to training and gear. Relevance is the highest of all categories (4.7), confirming that intent detection successfully directs safety queries to AAC content.

**Gear (pass rate 90%, overall 3.1/5):** Citation quality is low (1.8) for the same reason as training — gear review forum posts lack specific URLs. Factual accuracy (3.0) is lower than safety, reflecting that gear recommendation questions often require precise product comparisons that are not fully captured in short review snippets.

**Anti-Hallucination (pass rate 90%, overall 4.6/5):** The highest LLM judge score of all categories. 9 out of 10 out-of-domain queries were correctly refused with the standard response ("I don't have data on this in my climbing knowledge base"). The one failure (H06: "What climbing routes are on Mars?") received a 1/5 score — CruxBot answered rather than refusing, likely because the query contained the climbing-domain keyword "routes," which passed the domain check. This edge case illustrates a limitation of keyword-based domain detection versus semantic intent classification.

### 4.5 Qualitative Examples

**Successful route query (R09 — overall 5/5):**

> _Query:_ "What is the hardest sport route in El Potrero Chico?"
> _System:_ Retrieved specific Mountain Project routes with grades and clickable URLs. Answer named specific routes with accurate grades and descriptions. ✅

**Successful anti-hallucination (H03 — overall 5/5):**

> _Query:_ "How do I fix a bug in my Python code?"
> _System:_ "I don't have data on this in my climbing knowledge base. I can only answer questions related to rock climbing, routes, gear, and safety." ✅

**Failed anti-hallucination (H06 — overall 1/5):**

> _Query:_ "What climbing routes are on Mars?"
> _System:_ Answered the question rather than refusing — the keyword "routes" triggered climbing-domain retrieval. ❌

**Weak citation example (T01):**

> _Query:_ "How should I train finger strength for climbing?"
> _System:_ Provided relevant training advice (relevance 5/5) but cited `mountainproject.com/forum` as the source — a generic URL with no specificity. Citation score: 1/5. This is a data limitation, not a retrieval failure.

### 4.6 Human Evaluation Validation

To validate that GPT-4o scores align with human judgment, we conducted a human evaluation on 10 representative queries — 2 per category, one high-scoring and one lower-scoring — selected to cover the performance range of the system. Each team member scored independently using the same 4-dimension rubric, blind to the GPT-4o scores.

The purpose is not to replace the 50-query LLM evaluation, but to confirm that the automated judge is measuring the same qualities a human rater would penalize or reward. Queries were selected to include: one case where GPT-4o scored high (to confirm the score reflects genuine quality), one case where it scored low (to confirm the penalty is justified), and the H06 failure case (to confirm humans agree the Mars response was a hallucination failure).

Results of the human vs. GPT-4o score comparison will be reported in the final submission.

### 4.7 Limitations and Future Work

1. **Route coverage:** Routes in the database sometimes lack detailed beta (especially OpenBeta-only routes, which have no text description). A future version could integrate real-time scraping or Mountain Project's current API if it becomes available.
2. **Multi-turn dialogue:** The current system is stateless — each query is answered independently. A conversation memory layer (e.g., LangChain ConversationBufferMemory) would enable follow-up questions.
3. **Grade-based filtering:** While we normalize grades in queries, the retriever does not yet support numeric range filters (e.g., "5.10–5.11 routes"). This would require structured metadata filtering in ChromaDB rather than text-based matching.
4. **Evaluation scale:** 50 queries is sufficient for a course project but not statistically robust. A future iteration would expand to 500+ queries with multiple annotators and inter-annotator agreement scoring.

---

## 5. Individual Contributions

| Member                | Contribution                                                                                                                                                                                         |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sherwin Vahidimowlavi | Chunking pipeline (`src/chunking.py`), embedding pipeline (`src/embedding.py`), ChromaDB indexing of 382k vectors                                                                                    |
| Linxuan Li            | Retrieval logic (`src/retrieval.py`), RAG orchestration (`src/rag_pipeline.py`), Ollama integration, initial prompt design                                                                           |
| Lingyun Xiao          | Streamlit frontend (`streamlit_app.py`), FastAPI backend (`app.py`), GCP deployment, Docker containerization                                                                                         |
| Zongyang Li           | Data collection (6 sources, 338k entries), hybrid search (BM25+dense+RRF), query intent detection, grade normalization, prompt engineering, anti-hallucination design, evaluation suite (50 queries) |
| All                   | Writeup and oral delivery                                                                                                                                                                            |

---
