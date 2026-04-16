"""
CruxBot LLM-as-Judge Evaluation
=================================
Uses GPT-4o to score each RAG response on a rubric across 4 dimensions.
Requires: OPENAI_API_KEY environment variable

Usage:
    export OPENAI_API_KEY=sk-...
    python -u scripts/evaluate_llm_judge.py

    # Or pass key inline:
    OPENAI_API_KEY=sk-... python -u scripts/evaluate_llm_judge.py

Output:
    evaluation/llm_judge_results.json   — full scores per query
    Prints summary table to stdout
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # loads .env from project root

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_pipeline import answer

# ============================================================
# Config
# ============================================================
CHROMA_PATH = "data/chroma"
JUDGE_MODEL = "gpt-4o"
OUTPUT_PATH = "evaluation/llm_judge_results.json"

# ============================================================
# Rubric
# ============================================================
RUBRIC = """
You are an expert evaluator for a rock climbing AI assistant called CruxBot.
CruxBot uses Retrieval-Augmented Generation (RAG): it retrieves passages from a
climbing knowledge base (routes, forums, accident reports, gear reviews) and
generates an answer grounded in those passages.

Your job is to score CruxBot's response on the following rubric.
Return ONLY a valid JSON object — no extra text, no markdown fences.

== RUBRIC ==

1. relevance (1–5)
   Does the answer directly address what the user asked?
   1 = completely off-topic
   3 = partially relevant, some irrelevant content
   5 = fully on-topic, every sentence is relevant

2. factual_accuracy (1–5)
   Are the facts consistent with the retrieved sources provided?
   Do NOT penalize for information that simply isn't in the sources.
   Only penalize if the answer contradicts the sources or invents details.
   1 = multiple contradictions or invented facts
   3 = mostly accurate, minor unsupported claims
   5 = fully grounded in the sources, no fabrications

3. citation_quality (1–5)
   Does the answer properly use the retrieved sources?
   Are the source URLs specific and useful (not generic forum homepages)?
   1 = no citations, or all citations are generic/wrong
   3 = some specific citations, some generic
   5 = all citations are specific, clickable, and match the content

4. completeness (1–5)
   Does the answer fully address the question given what the sources contain?
   If the answer says "I don't have data" but sources are relevant, penalize.
   If sources genuinely don't contain the answer, a refusal is correct.
   1 = answer is a stub or misses the main point
   3 = covers the main point but misses important aspects
   5 = comprehensive given the available sources

== SPECIAL CASE: Anti-hallucination queries ==
If the query is clearly outside the climbing domain (e.g. stock prices, cooking,
politics), the CORRECT response is a refusal like "I don't have data on this."
In that case:
   - If CruxBot correctly refuses → score all dimensions 5
   - If CruxBot answers anyway (hallucination) → score all dimensions 1

== OUTPUT FORMAT ==
{
  "relevance": <1-5>,
  "relevance_reason": "<one sentence>",
  "factual_accuracy": <1-5>,
  "factual_accuracy_reason": "<one sentence>",
  "citation_quality": <1-5>,
  "citation_quality_reason": "<one sentence>",
  "completeness": <1-5>,
  "completeness_reason": "<one sentence>",
  "overall": <1-5>,
  "overall_reason": "<one sentence summary>"
}
""".strip()


# ============================================================
# Test queries (same 50 as evaluate.py)
# ============================================================
TEST_QUERIES = [
    # Route
    {"id": "R01", "query": "Recommend a 5.10 sport climbing route in California", "category": "route", "expect_hallucination": False},
    {"id": "R02", "query": "What are some good beginner trad routes in Red River Gorge?", "category": "route", "expect_hallucination": False},
    {"id": "R03", "query": "Best bouldering problems around V4 in Bishop California", "category": "route", "expect_hallucination": False},
    {"id": "R04", "query": "Recommend a multi-pitch route in Yosemite for intermediate climbers", "category": "route", "expect_hallucination": False},
    {"id": "R05", "query": "What are some classic 5.12 routes in Smith Rock Oregon?", "category": "route", "expect_hallucination": False},
    {"id": "R06", "query": "Find me a 5.8 sport route in Joshua Tree", "category": "route", "expect_hallucination": False},
    {"id": "R07", "query": "What are popular ice climbing routes in Colorado?", "category": "route", "expect_hallucination": False},
    {"id": "R08", "query": "Suggest a beginner-friendly climbing route in Utah", "category": "route", "expect_hallucination": False},
    {"id": "R09", "query": "What is the hardest sport route in El Potrero Chico?", "category": "route", "expect_hallucination": False},
    {"id": "R10", "query": "Recommend a V0-V2 bouldering area near San Francisco", "category": "route", "expect_hallucination": False},
    # Training
    {"id": "T01", "query": "How should I train finger strength for climbing?", "category": "training", "expect_hallucination": False},
    {"id": "T02", "query": "What is the best hangboard routine for intermediate climbers?", "category": "training", "expect_hallucination": False},
    {"id": "T03", "query": "How do I improve my footwork on overhangs?", "category": "training", "expect_hallucination": False},
    {"id": "T04", "query": "Tips for climbing slab routes?", "category": "training", "expect_hallucination": False},
    {"id": "T05", "query": "How to prevent climbing injuries in fingers and elbows?", "category": "training", "expect_hallucination": False},
    {"id": "T06", "query": "What is a good weekly training schedule for V5 bouldering?", "category": "training", "expect_hallucination": False},
    {"id": "T07", "query": "How do I build endurance for long multi-pitch routes?", "category": "training", "expect_hallucination": False},
    {"id": "T08", "query": "What stretches help with hip flexibility for climbing?", "category": "training", "expect_hallucination": False},
    {"id": "T09", "query": "How to overcome a climbing plateau at 5.11?", "category": "training", "expect_hallucination": False},
    {"id": "T10", "query": "Should I campus board as a beginner?", "category": "training", "expect_hallucination": False},
    # Safety
    {"id": "S01", "query": "What are the most common lead climbing accidents?", "category": "safety", "expect_hallucination": False},
    {"id": "S02", "query": "How do I safely clean a sport climbing anchor?", "category": "safety", "expect_hallucination": False},
    {"id": "S03", "query": "What causes rappelling accidents in climbing?", "category": "safety", "expect_hallucination": False},
    {"id": "S04", "query": "How to avoid rockfall injuries while climbing outdoors?", "category": "safety", "expect_hallucination": False},
    {"id": "S05", "query": "What happened in climbing accidents at Red River Gorge?", "category": "safety", "expect_hallucination": False},
    {"id": "S06", "query": "How to tie a safe figure-eight knot?", "category": "safety", "expect_hallucination": False},
    {"id": "S07", "query": "What are common belaying mistakes that lead to accidents?", "category": "safety", "expect_hallucination": False},
    {"id": "S08", "query": "Fatal climbing accidents caused by equipment failure", "category": "safety", "expect_hallucination": False},
    {"id": "S09", "query": "How dangerous is free soloing?", "category": "safety", "expect_hallucination": False},
    {"id": "S10", "query": "What should I do if my climbing partner falls and is injured?", "category": "safety", "expect_hallucination": False},
    # Gear
    {"id": "G01", "query": "What is the best belay device for multi-pitch climbing?", "category": "gear", "expect_hallucination": False},
    {"id": "G02", "query": "La Sportiva vs Scarpa climbing shoes comparison", "category": "gear", "expect_hallucination": False},
    {"id": "G03", "query": "What climbing rope should I buy for sport climbing?", "category": "gear", "expect_hallucination": False},
    {"id": "G04", "query": "Best harness for beginners?", "category": "gear", "expect_hallucination": False},
    {"id": "G05", "query": "Review of Black Diamond ATC Guide belay device", "category": "gear", "expect_hallucination": False},
    {"id": "G06", "query": "What helmet should I use for outdoor climbing?", "category": "gear", "expect_hallucination": False},
    {"id": "G07", "query": "Best chalk bag for bouldering?", "category": "gear", "expect_hallucination": False},
    {"id": "G08", "query": "How to choose quickdraws for sport climbing?", "category": "gear", "expect_hallucination": False},
    {"id": "G09", "query": "What crash pad should I buy for outdoor bouldering?", "category": "gear", "expect_hallucination": False},
    {"id": "G10", "query": "Are assisted braking belay devices safer than tube style?", "category": "gear", "expect_hallucination": False},
    # Anti-hallucination
    {"id": "H01", "query": "What is the best restaurant near Yosemite Valley?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H02", "query": "Who won the 2024 NBA finals?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H03", "query": "How do I fix a bug in my Python code?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H04", "query": "What is the weather forecast for tomorrow in New York?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H05", "query": "Recommend a good hotel in Las Vegas", "category": "hallucination", "expect_hallucination": True},
    {"id": "H06", "query": "What climbing routes are on Mars?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H07", "query": "Tell me about the history of the Roman Empire", "category": "hallucination", "expect_hallucination": True},
    {"id": "H08", "query": "What is the stock price of Apple today?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H09", "query": "How to cook a perfect steak?", "category": "hallucination", "expect_hallucination": True},
    {"id": "H10", "query": "Recommend climbing routes on Mount Everest summit ridge", "category": "hallucination", "expect_hallucination": True},
]


# ============================================================
# Judge call
# ============================================================
def judge(client, query, rag_answer, sources, expect_hallucination):
    """Call GPT-4o to score a single RAG response. Returns dict of scores."""
    sources_text = "\n".join(
        f"  - [{s.get('title', 'Source')}] {s.get('url', '')}" for s in sources[:5]
    ) or "  (no sources retrieved)"

    user_message = f"""
== USER QUERY ==
{query}

== CRUXBOT ANSWER ==
{rag_answer}

== RETRIEVED SOURCES ==
{sources_text}

== IS THIS AN ANTI-HALLUCINATION TEST? ==
{"YES — the correct response is a refusal, not a climbing answer." if expect_hallucination else "NO — this is a legitimate climbing question."}

Score the response using the rubric. Return only JSON.
""".strip()

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model=JUDGE_MODEL,
                messages=[
                    {"role": "system", "content": RUBRIC},
                    {"role": "user", "content": user_message},
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            if attempt == 2:
                print(f"    [Judge error after 3 attempts] {e}")
                return None
            time.sleep(2 ** attempt)


# ============================================================
# Main
# ============================================================
def run():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("  export OPENAI_API_KEY=sk-...")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("=" * 70)
    print("CruxBot LLM-as-Judge Evaluation")
    print(f"  Judge model : {JUDGE_MODEL}")
    print(f"  Queries     : {len(TEST_QUERIES)}")
    print(f"  ChromaDB    : {CHROMA_PATH}")
    print("=" * 70)

    results = []
    category_scores = {}

    for i, tq in enumerate(TEST_QUERIES):
        qid = tq["id"]
        query = tq["query"]
        category = tq["category"]

        print(f"\n[{i+1:02d}/{len(TEST_QUERIES)}] {qid} | {query[:55]}...")

        # --- Step 1: Get CruxBot answer ---
        try:
            rag_result = answer(query, top_k=5, chroma_path=CHROMA_PATH)
            rag_answer = rag_result.get("answer", "")
            sources = rag_result.get("sources", [])
        except Exception as e:
            print(f"  [RAG error] {e}")
            rag_answer = f"ERROR: {e}"
            sources = []

        print(f"  RAG answer  : {rag_answer[:80]}...")

        # --- Step 2: Judge ---
        scores = judge(client, query, rag_answer, sources, tq["expect_hallucination"])

        if scores:
            overall = scores.get("overall", 0)
            print(f"  Scores → relevance={scores.get('relevance')} | "
                  f"accuracy={scores.get('factual_accuracy')} | "
                  f"citation={scores.get('citation_quality')} | "
                  f"completeness={scores.get('completeness')} | "
                  f"overall={overall}")
        else:
            scores = {}
            overall = 0
            print("  Scores → [judge failed]")

        entry = {
            "id": qid,
            "category": category,
            "query": query,
            "answer": rag_answer[:600],
            "sources": [s.get("url", "") for s in sources[:5]],
            "expect_hallucination": tq["expect_hallucination"],
            "scores": scores,
        }
        results.append(entry)

        # Accumulate per-category
        if category not in category_scores:
            category_scores[category] = {
                "relevance": [], "factual_accuracy": [],
                "citation_quality": [], "completeness": [], "overall": []
            }
        for dim in ["relevance", "factual_accuracy", "citation_quality", "completeness", "overall"]:
            val = scores.get(dim)
            if val is not None:
                category_scores[category][dim].append(val)

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY (GPT-4o Judge, 1-5 scale)")
    print("=" * 70)

    all_scores = {"relevance": [], "factual_accuracy": [], "citation_quality": [], "completeness": [], "overall": []}
    for r in results:
        for dim in all_scores:
            val = r["scores"].get(dim)
            if val is not None:
                all_scores[dim].append(val)

    print("\nOverall averages:")
    for dim, vals in all_scores.items():
        if vals:
            print(f"  {dim:<20} {sum(vals)/len(vals):.2f} / 5.00")

    print("\nBy category:")
    header = f"  {'Category':<15} {'Relevance':>9} {'Accuracy':>9} {'Citation':>9} {'Complete':>9} {'Overall':>9}"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for cat, dims in sorted(category_scores.items()):
        def avg(lst): return f"{sum(lst)/len(lst):.2f}" if lst else "  N/A"
        print(f"  {cat:<15} {avg(dims['relevance']):>9} {avg(dims['factual_accuracy']):>9} "
              f"{avg(dims['citation_quality']):>9} {avg(dims['completeness']):>9} {avg(dims['overall']):>9}")

    # Estimate cost
    total_queries = len(results)
    est_input_tokens = total_queries * 1100
    est_output_tokens = total_queries * 300
    est_cost = (est_input_tokens * 2.50 + est_output_tokens * 10.00) / 1_000_000
    print(f"\nEstimated GPT-4o cost: ~${est_cost:.3f}")

    # Save
    output = {
        "judge_model": JUDGE_MODEL,
        "total_queries": total_queries,
        "overall_averages": {dim: round(sum(v)/len(v), 2) if v else None for dim, v in all_scores.items()},
        "by_category": {
            cat: {dim: round(sum(v)/len(v), 2) if v else None for dim, v in dims.items()}
            for cat, dims in category_scores.items()
        },
        "results": results,
    }
    os.makedirs("evaluation", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nFull results saved to: {OUTPUT_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    run()
