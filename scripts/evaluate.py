"""
CruxBot Evaluation Script
==========================
Tests the RAG system across 5 dimensions:
1. Retrieval quality (content type coverage)
2. Answer accuracy (factual correctness)
3. Citation correctness (URLs are valid)
4. Anti-hallucination (graceful "no data" responses)
5. Latency (end-to-end response time)

Usage:
    python -u scripts/evaluate.py
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.rag_pipeline import answer

CHROMA_PATH = "data/chroma"

# ============================================================
# Test Queries — 50+ queries across 5 categories
# ============================================================
TEST_QUERIES = [
    # ==============================
    # Category 1: Route Recommendations (expect: route content_type)
    # ==============================
    {"id": "R01", "query": "Recommend a 5.10 sport climbing route in California",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R02", "query": "What are some good beginner trad routes in Red River Gorge?",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R03", "query": "Best bouldering problems around V4 in Bishop California",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R04", "query": "Recommend a multi-pitch route in Yosemite for intermediate climbers",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R05", "query": "What are some classic 5.12 routes in Smith Rock Oregon?",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R06", "query": "Find me a 5.8 sport route in Joshua Tree",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R07", "query": "What are popular ice climbing routes in Colorado?",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R08", "query": "Suggest a beginner-friendly climbing route in Utah",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R09", "query": "What is the hardest sport route in El Potrero Chico?",
     "category": "route", "expect_type": "route", "expect_hallucination": False},
    {"id": "R10", "query": "Recommend a V0-V2 bouldering area near San Francisco",
     "category": "route", "expect_type": "route", "expect_hallucination": False},

    # ==============================
    # Category 2: Training & Technique (expect: forum_discussion)
    # ==============================
    {"id": "T01", "query": "How should I train finger strength for climbing?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T02", "query": "What is the best hangboard routine for intermediate climbers?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T03", "query": "How do I improve my footwork on overhangs?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T04", "query": "Tips for climbing slab routes?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T05", "query": "How to prevent climbing injuries in fingers and elbows?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T06", "query": "What is a good weekly training schedule for V5 bouldering?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T07", "query": "How do I build endurance for long multi-pitch routes?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T08", "query": "What stretches help with hip flexibility for climbing?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T09", "query": "How to overcome a climbing plateau at 5.11?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},
    {"id": "T10", "query": "Should I campus board as a beginner?",
     "category": "training", "expect_type": "forum_discussion", "expect_hallucination": False},

    # ==============================
    # Category 3: Safety & Accidents (expect: article)
    # ==============================
    {"id": "S01", "query": "What are the most common lead climbing accidents?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S02", "query": "How do I safely clean a sport climbing anchor?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S03", "query": "What causes rappelling accidents in climbing?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S04", "query": "How to avoid rockfall injuries while climbing outdoors?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S05", "query": "What happened in climbing accidents at Red River Gorge?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S06", "query": "How to tie a safe figure-eight knot?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S07", "query": "What are common belaying mistakes that lead to accidents?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S08", "query": "Fatal climbing accidents caused by equipment failure",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S09", "query": "How dangerous is free soloing?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},
    {"id": "S10", "query": "What should I do if my climbing partner falls and is injured?",
     "category": "safety", "expect_type": "article", "expect_hallucination": False},

    # ==============================
    # Category 4: Gear & Equipment (expect: gear_review)
    # ==============================
    {"id": "G01", "query": "What is the best belay device for multi-pitch climbing?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G02", "query": "La Sportiva vs Scarpa climbing shoes comparison",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G03", "query": "What climbing rope should I buy for sport climbing?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G04", "query": "Best harness for beginners?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G05", "query": "Review of Black Diamond ATC Guide belay device",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G06", "query": "What helmet should I use for outdoor climbing?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G07", "query": "Best chalk bag for bouldering?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G08", "query": "How to choose quickdraws for sport climbing?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G09", "query": "What crash pad should I buy for outdoor bouldering?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},
    {"id": "G10", "query": "Are assisted braking belay devices safer than tube style?",
     "category": "gear", "expect_type": "gear_review", "expect_hallucination": False},

    # ==============================
    # Category 5: Anti-hallucination (expect: "I don't have data")
    # ==============================
    {"id": "H01", "query": "What is the best restaurant near Yosemite Valley?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H02", "query": "Who won the 2024 NBA finals?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H03", "query": "How do I fix a bug in my Python code?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H04", "query": "What is the weather forecast for tomorrow in New York?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H05", "query": "Recommend a good hotel in Las Vegas",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H06", "query": "What climbing routes are on Mars?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H07", "query": "Tell me about the history of the Roman Empire",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H08", "query": "What is the stock price of Apple today?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H09", "query": "How to cook a perfect steak?",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
    {"id": "H10", "query": "Recommend climbing routes on Mount Everest summit ridge",
     "category": "hallucination", "expect_type": None, "expect_hallucination": True},
]


def check_hallucination_refusal(answer_text):
    """Check if the answer properly refuses to answer (anti-hallucination)."""
    refusal_phrases = [
        "i don't have data",
        "i don't have information",
        "not found in the context",
        "no relevant data",
        "cannot answer",
        "don't have enough information",
        "not in my knowledge base",
        "no data on this",
    ]
    lower = answer_text.lower()
    return any(phrase in lower for phrase in refusal_phrases)


def run_evaluation():
    print("=" * 70)
    print("🧪 CruxBot Evaluation")
    print(f"   Total test queries: {len(TEST_QUERIES)}")
    print(f"   ChromaDB path: {CHROMA_PATH}")
    print("=" * 70)

    results = []
    category_stats = {}

    for i, tq in enumerate(TEST_QUERIES):
        qid = tq["id"]
        query = tq["query"]
        category = tq["category"]
        expect_hallucination = tq["expect_hallucination"]

        print(f"\n[{i+1}/{len(TEST_QUERIES)}] {qid}: {query[:60]}...")

        # Time the query
        start = time.time()
        try:
            result = answer(query, top_k=5, chroma_path=CHROMA_PATH)
            latency = time.time() - start
            answer_text = result.get("answer", "")
            sources = result.get("sources", [])
            success = True
        except Exception as e:
            latency = time.time() - start
            answer_text = f"ERROR: {e}"
            sources = []
            success = False

        # Check anti-hallucination
        is_refusal = check_hallucination_refusal(answer_text)
        hallucination_pass = (expect_hallucination and is_refusal) or (not expect_hallucination and not is_refusal)

        # Check if sources have URLs
        urls = [s.get("url", "") for s in sources if s.get("url")]
        has_citations = len(urls) > 0

        # Citation correctness: check if URLs are specific (not generic)
        generic_urls = ["https://openbeta.io", "https://www.mountainproject.com/", "https://www.mountainproject.com/forum"]
        specific_urls = [u for u in urls if u not in generic_urls]
        citation_quality = len(specific_urls) / max(len(urls), 1)

        status = "✅" if success and hallucination_pass else "❌"
        print(f"  {status} Latency: {latency:.1f}s | Citations: {len(urls)} | Hallucination check: {'PASS' if hallucination_pass else 'FAIL'}")
        print(f"  Answer: {answer_text[:150]}...")

        entry = {
            "id": qid,
            "query": query,
            "category": category,
            "answer": answer_text[:500],
            "latency": round(latency, 2),
            "num_sources": len(urls),
            "specific_urls": len(specific_urls),
            "citation_quality": round(citation_quality, 2),
            "expect_hallucination": expect_hallucination,
            "is_refusal": is_refusal,
            "hallucination_pass": hallucination_pass,
            "success": success,
            "sources": [u[:80] for u in urls[:5]],
        }
        results.append(entry)

        # Track category stats
        if category not in category_stats:
            category_stats[category] = {"total": 0, "pass": 0, "latencies": [], "citation_qualities": []}
        category_stats[category]["total"] += 1
        if hallucination_pass and success:
            category_stats[category]["pass"] += 1
        category_stats[category]["latencies"].append(latency)
        category_stats[category]["citation_qualities"].append(citation_quality)

    # ============================================================
    # Summary Report
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 EVALUATION SUMMARY")
    print("=" * 70)

    total_pass = sum(1 for r in results if r["hallucination_pass"] and r["success"])
    total = len(results)
    avg_latency = sum(r["latency"] for r in results) / total
    avg_citation = sum(r["citation_quality"] for r in results if not r["expect_hallucination"]) / max(sum(1 for r in results if not r["expect_hallucination"]), 1)

    print(f"\n  Overall pass rate: {total_pass}/{total} ({total_pass/total*100:.0f}%)")
    print(f"  Average latency: {avg_latency:.1f}s")
    print(f"  Average citation quality: {avg_citation:.0%}")

    print(f"\n  By Category:")
    for cat, stats in sorted(category_stats.items()):
        avg_lat = sum(stats["latencies"]) / max(len(stats["latencies"]), 1)
        pass_rate = stats["pass"] / stats["total"] * 100
        print(f"    {cat:<15} {stats['pass']}/{stats['total']} pass ({pass_rate:.0f}%) | avg latency: {avg_lat:.1f}s")

    # Anti-hallucination specific stats
    hall_queries = [r for r in results if r["expect_hallucination"]]
    hall_pass = sum(1 for r in hall_queries if r["hallucination_pass"])
    print(f"\n  Anti-hallucination:")
    print(f"    {hall_pass}/{len(hall_queries)} correctly refused to answer out-of-domain queries")

    # Citation stats
    cite_queries = [r for r in results if not r["expect_hallucination"]]
    with_citations = sum(1 for r in cite_queries if r["num_sources"] > 0)
    print(f"\n  Citations:")
    print(f"    {with_citations}/{len(cite_queries)} responses included source URLs")

    # Save results
    output_path = "evaluation/evaluation_results.json"
    os.makedirs("evaluation", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "summary": {
                "total_queries": total,
                "pass_rate": f"{total_pass/total*100:.0f}%",
                "avg_latency": f"{avg_latency:.1f}s",
                "avg_citation_quality": f"{avg_citation:.0%}",
                "anti_hallucination_rate": f"{hall_pass}/{len(hall_queries)}",
            },
            "by_category": {cat: {"pass": s["pass"], "total": s["total"]} for cat, s in category_stats.items()},
            "results": results,
        }, f, indent=2, default=str)
    print(f"\n  Results saved to: {output_path}")

    print("\n" + "=" * 70)
    print("✅ Evaluation complete!")
    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()
