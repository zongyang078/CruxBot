# CruxBot Human Evaluation — 10 Representative Queries

**Purpose:** Validate the GPT-4o automated evaluation by comparing human scores against LLM scores on 10 representative queries (2 per category).

**Instructions:**
- Read each query and CruxBot's answer carefully
- Score on 4 dimensions using the rubric below (1–5)
- Write a brief reason (1 sentence) for each score
- Do NOT look at the GPT-4o scores until you have finished

**Rater name:** Lingyun Xiao
**Date:** 2026-04-15

---

## Scoring Rubric

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Relevance** | Completely off-topic | Partially relevant | Fully addresses the question |
| **Factual Accuracy** | Contradicts sources / fabricated | Mostly accurate, minor unsupported claims | Fully grounded in sources, no fabrications |
| **Citation Quality** | No citations or all generic URLs | Some specific, some generic | All specific, clickable, matching content |
| **Completeness** | Misses the main point | Covers main point, misses details | Comprehensive given available sources |

**Special rule for anti-hallucination queries (H03, H06):**
If the question is clearly outside the climbing domain, the correct answer is a refusal ("I don't have data on this").
- Correct refusal → score all dimensions **5**
- Answered anyway (hallucination) → score all dimensions **1**

---

## Category 1: Route

### R01 — High performing example
**Query:** Recommend a 5.10 sport climbing route in California

**CruxBot Answer:**
> Based on the provided context, there are two 5.10 sport climbing routes mentioned:
>
> 1. Slab Middle (5.10) located in California > Northeast California > Castle Crags > Indian Springs Canyon > Pin Cushion Wall [2]
> 2. Slab RHS (5.10) located in California > Northeast California > Castle Crags > Indian Springs Canyon > Pin Cushion Wall [4]
>
> Both routes are located in the same area, Castle Crags. If you're looking for a 5.10 sport climbing route in California, I would recommend either of these two options.

**Sources cited:**
- https://openbeta.io/climb/d2a1374a-1615-5a2f-92f4-0cddab8ab8f3
- https://openbeta.io/climb/829e606d-c49b-5e17-aaa7-4105529a6ae0

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly answers the request for a 5.10 sport route in California with specific options. |
| Factual Accuracy | 4 | Route names and grades match sources; Castle Crags is a real area in NE California, no fabrication. |
| Citation Quality | 4 | Specific OpenBeta URLs per route; slightly less convenient than Mountain Project links but clickable and verifiable. |
| Completeness | 4 | Two options with full location hierarchy provided; could mention more popular California sport crags (e.g., Yosemite, Tahoe), but the answer is honest about what the database returned. |
| **Overall** | **4** | Solid, grounded answer with specific citations — slightly limited by database coverage but no errors. |

> **Note:** Human overall = 4, GPT-4o = 5. Minor disagreement — GPT-4o gave full marks for completeness, but from a practical standpoint Castle Crags is an obscure recommendation for a California 5.10 query compared to areas like Yosemite or Tahoe. This reflects a database coverage gap, not a generation failure.

*GPT-4o scores: Relevance=5, Accuracy=5, Citation=4, Completeness=5, Overall=5*

---

### R03 — Lower performing example
**Query:** Best bouldering problems around V4 in Bishop California

**CruxBot Answer:**
> According to the context, there are three V4 bouldering climbing routes mentioned in Bishop, California:
>
> 1. Problem A (Grade: V4) - located in Mammoth Lakes Area > Mammoth Lakes Bouldering > TJ Lake > Medicine Boulder [3]
> 2. Peanut arete (Grade: V4) - located in Bishop Peak > Bishop Peak Bouldering > Boulder In The Woods [4]
> 3. Problem A (Grade: V4) - located in Volcanic Tablelands (Happy/Sad Boulders) > Happy Boulders > West Rim Area > Frontierland > Highbrow Area [5]

**Sources cited:**
- https://openbeta.io/climb/01d9a50a-b8db-51d4-8dbc-b38e6c7cde84
- https://openbeta.io/climb/8e79b658-9d00-514d-a7d8-e86f987ca127

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 3 | Attempts to answer but includes areas that are not Bishop, CA. |
| Factual Accuracy | 2 | "Bishop Peak" is in San Luis Obispo (~400 miles from Bishop); Mammoth Lakes is near Bishop but is a different town — only item #3 (Volcanic Tablelands/Happy Boulders) is actually in Bishop. |
| Citation Quality | 2 | URLs are specific to each problem but link to problems not actually in Bishop, so citations are misleading. |
| Completeness | 2 | Misses the Buttermilks (the most famous Bishop V4 area) entirely; only 1 of 3 listed problems is genuinely in Bishop. |
| **Overall** | **2** | Geographic confusion significantly undermines the answer's usefulness despite the correct grade. |

> **Note:** Human and GPT-4o agree on overall=2. GPT-4o's low score is well-justified — this confirms the automated judge correctly penalizes geographic inaccuracy.

*GPT-4o scores: Relevance=3, Accuracy=2, Citation=2, Completeness=2, Overall=2*

---

## Category 2: Training

### T09 — Higher performing example
**Query:** How to overcome a climbing plateau at 5.11?

**CruxBot Answer:**
> Based on the provided context, it seems like you're looking for advice on how to overcome a climbing plateau at 5.11. From [1], I see that someone recommended focusing on becoming a better climber rather than just trying to get stronger. This suggests that plateaus might be due to a lack of proper training or technique.
>
> In [3], another user shared their experience of improving their climbing skills without formal training, by reading about different climbing styles and gradually increasing the difficulty of climbs. They also emphasized the importance of learning good style and technique, which can help improve overall climbing ability.

**Sources cited:**
- https://www.mountainproject.com/forum
- https://www.mountainproject.com/forum

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly addresses the plateau question with actionable advice. |
| Factual Accuracy | 3 | Advice (technique over strength, progressive difficulty) is sound climbing wisdom, but attributed loosely to forum posts that can't be verified via the generic URLs. |
| Citation Quality | 2 | All citations are generic mountainproject.com/forum — the Reddit URL that GPT-4o cited as "3" is not visible here; both visible citations are generic. |
| Completeness | 3 | Covers technique and progressive difficulty but omits key strategies like structured hangboard training, climbing with better partners, or projecting specific routes. |
| **Overall** | **3** | Relevant and reasonable but lacks depth and specific sourcing. |

> **Note:** Human overall = 3 vs GPT-4o = 4. Disagreement on citation quality — GPT-4o was more lenient. Human score reflects that generic forum URLs provide no verifiable grounding.

*GPT-4o scores: Relevance=5, Accuracy=4, Citation=3, Completeness=4, Overall=4*

---

### T01 — Citation limitation example
**Query:** How should I train finger strength for climbing?

**CruxBot Answer:**
> Based on the provided context, it seems that hangboards are a popular training tool among climbers to improve finger strength. Several users mention using hangboards at home or in gyms, and some share their experiences with using them.
>
> One user mentions specifically using hangboards with soft rounded edges to target sloper holds, which can be beneficial for building wrist strength and overall climbing technique ([2]).
>
> Another user notes that training gloves might not be necessary if you're planning to train indoors, as liquid chalk can provide sufficient grip ([4]).

**Sources cited:**
- https://www.mountainproject.com/forum *(generic — no specific post URL available)*
- https://www.reddit.com/r/bouldering/comments/1r3vwce/tips_on_technique/

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly answers the finger strength training question. |
| Factual Accuracy | 3 | Hangboard advice is generally correct, but "soft rounded edges for wrist strength" conflates finger/pulley strength with wrist strength — a minor but real inaccuracy. |
| Citation Quality | 1 | One forum URL is generic (can't trace to specific post); the Reddit link is specific but the response doesn't clearly connect it to the claims made. |
| Completeness | 3 | Mentions hangboards but omits key details: max hangs vs. repeater protocols, rest period requirements, and the common injury risk for beginners. |
| **Overall** | **3** | Relevant and not harmful, but lacks the specificity a climber would need to actually implement the advice. |

> **Note:** Human and GPT-4o agree on overall=3. The citation quality issue is a confirmed data limitation — not a failure of the retrieval system itself.

*GPT-4o scores: Relevance=5, Accuracy=3, Citation=1, Completeness=4, Overall=3*

---

## Category 3: Safety

### S07 — High performing example
**Query:** What are common belaying mistakes that lead to accidents?

**CruxBot Answer:**
> According to the American Alpine Club, common belaying mistakes that lead to accidents include [1]:
>
> - Inadequate anchor systems or anchor failure
> - Inadequate backup for rappels
> - Rappelling off the end of the rope(s) due to uneven ropes
> - Rappel device issues, Stranded due to inadequate rappel rope length
> - Harness/belay loop failure
>
> Additionally, [2] emphasizes the importance of preventing lowering accidents by taking simple steps:
> 1. Make a plan and communicate it with your belayer.
> 2. Tie a stopper knot in the belayer's end of the rope or tie the rope to the harness.

**Sources cited:**
- https://publications.americanalpineclub.org/articles/13201200200
- https://publications.americanalpineclub.org/articles/13201214710
- https://publications.americanalpineclub.org/articles/13201216254

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly and specifically answers the question about belaying mistakes. |
| Factual Accuracy | 5 | All claims are directly attributed to AAC accident reports — the most authoritative source for climbing accident data. |
| Citation Quality | 5 | Specific AAC publication URLs with article IDs, fully verifiable and directly relevant to the content. |
| Completeness | 5 | Covers multiple failure modes (anchor, rappel, equipment, harness) and includes concrete preventive steps. |
| **Overall** | **5** | Best-case RAG output: authoritative source, specific citations, comprehensive and actionable answer. |

> **Note:** Human and GPT-4o both agree on 5/5. This demonstrates that when the database has high-quality, well-cited content (AAC articles), the system performs excellently. This validates that our retrieval and generation pipeline works well when source quality is high.

*GPT-4o scores: Relevance=5, Accuracy=5, Citation=5, Completeness=5, Overall=5*

---

### S05 — Lower performing example
**Query:** What happened in climbing accidents at Red River Gorge?

**CruxBot Answer:**
> As a climbing assistant, I've reviewed the provided context, which includes information about various routes and locations within Red River Gorge, Kentucky. Since there is no specific mention of accidents or incidents related to climbing, I don't have any concrete data on climbing accidents at Red River Gorge.
>
> However, I can suggest some general tips for climbers to minimize risks and ensure a safe climbing experience:
> 1. Always wear proper gear, including helmets, harnesses, and shoes.
> 2. Inspect the route and surrounding area before starting your climb.

**Sources cited:**
- https://www.mountainproject.com/route/105880966/new-red-river
- https://www.mountainproject.com/route/108384240/weathertop-stings

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 2 | Correctly states it lacks RRG-specific accident data, but then pivots to generic safety tips rather than attempting to retrieve relevant AAC articles. |
| Factual Accuracy | 4 | Does not fabricate accident data — correctly reports absence of specific data, and the generic tips are accurate. |
| Citation Quality | 1 | Route URLs are completely irrelevant to an accident report query — they add no value to the response. |
| Completeness | 2 | Fails to answer the core question; AAC database contains RRG accident reports that should have been retrieved by the safety intent detector. |
| **Overall** | **2** | Honest non-answer but a retrieval failure — the system should have surfaced AAC accident articles for a location-specific safety query. |

> **Note:** Human and GPT-4o agree on overall=3 / human=2. Slight disagreement: human penalizes more harshly because the AAC data DOES contain RRG accident reports that weren't retrieved, suggesting a retrieval gap rather than a genuine "no data" situation.

*GPT-4o scores: Relevance=3, Accuracy=5, Citation=1, Completeness=2, Overall=3*

---

## Category 4: Gear

### G05 — Higher performing example
**Query:** Review of Black Diamond ATC Guide belay device

**CruxBot Answer:**
> Based on the provided context, there is a gear review for the Black Diamond ATC-Guide belay device on trailspace.com with a rating of 5.0/5. According to this review, the ATC-Guide is a lightweight and nice evolution from the ATC. It allows for direct belaying off anchors, which helps in keeping the second safe. Additionally, it's easy to incorporate into the anchor system and easy to rappel from single or double line rappels.
>
> Source: [5] Trailspace.com - Gear Review - Black Diamond atc-guide (rated 5.0/5)

**Sources cited:**
- https://www.mountainproject.com/forum *(generic)*

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly reviews the requested device with specific features and rating. |
| Factual Accuracy | 4 | ATC-Guide features described (guide mode, lightweight, easy rappel) are accurate; rating is correctly attributed to Trailspace. |
| Citation Quality | 2 | The answer mentions Trailspace as source, but the cited URL is a generic MP forum link — the actual Trailspace URL was not passed through, creating a mismatch. |
| Completeness | 3 | Covers the essentials (rating, guide mode, rappel) but omits rope diameter compatibility, weight specs, and comparison to competitors (Reverso, Grigri). |
| **Overall** | **3** | Useful and accurate answer undermined by a citation mismatch — the content mentions Trailspace but the URL shown is a generic forum link. |

> **Note:** Human overall=3 vs GPT-4o=4. The citation mismatch (Trailspace content cited with forum URL) is a concrete problem that human raters notice more readily than the automated judge.

*GPT-4o scores: Relevance=5, Accuracy=3, Citation=3, Completeness=4, Overall=4*

---

### G01 — Citation limitation example
**Query:** What is the best belay device for multi-pitch climbing?

**CruxBot Answer:**
> Based on the context, it's clear that the conversation revolves around belay devices and multi-pitch climbing. Here's a summary:
>
> - The GriGri+ is designed for multi-pitch climbing [1].
> - Reverso and ATC Guide are mentioned as options to consider [2].
> - The Mammut Bionic has the lowest friction in guide mode among tube-style devices, while the Gigajul offers maximum versatility [3].
> - The Gigi/Grigri setup is recommended for short multi-pitch climbs with single ropes [3].

**Sources cited:**
- https://www.mountainproject.com/forum *(generic — no specific post URL available)*
- https://www.mountainproject.com/forum *(generic)*

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Directly addresses the question with multiple device options for multi-pitch. |
| Factual Accuracy | 3 | Device options are legitimate choices, but "Mammut Bionic has lowest friction in guide mode" is a specific claim that can't be verified from generic forum sources. |
| Citation Quality | 1 | All sources are generic forum URLs — a confirmed data limitation for MP forum posts. |
| Completeness | 3 | Lists options but doesn't explain key trade-offs for multi-pitch: weight, assisted braking relevance for long runouts, or half-rope compatibility for alpine/trad. |
| **Overall** | **3** | Covers the topic but lacks verifiable sourcing and actionable comparison. |

> **Note:** Human and GPT-4o agree on overall=3. Citation quality is a known data limitation — the Kaggle forum dataset lacks post-level URLs.

*GPT-4o scores: Relevance=5, Accuracy=3, Citation=1, Completeness=4, Overall=3*

---

## Category 5: Anti-Hallucination

### H03 — Correct refusal (expected: all 5s)
**Query:** How do I fix a bug in my Python code?

**CruxBot Answer:**
> I don't have data on this in my climbing knowledge base. I can only answer questions about rock climbing.

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5 | Correctly identifies this as outside the climbing domain. |
| Factual Accuracy | 5 | The refusal statement is accurate — no fabrication attempted. |
| Citation Quality | 5 | No citation needed for a refusal; not penalized. |
| Completeness | 5 | Clean, unambiguous refusal — no need for further elaboration. |
| **Overall** | **5** | Perfect anti-hallucination response: concise, correct, not over-explained. |

> **Note:** Human and GPT-4o agree on 5/5. This is the ideal behavior — short, clear refusal without attempting to answer.

*GPT-4o scores: All dimensions = 5*

---

### H06 — Edge case: query misinterpretation (not hallucination)
**Query:** What climbing routes are on Mars?

**CruxBot Answer:**
> Based on the provided context, I found several routes related to "Mars":
>
> 1. **Mars Traverse** (V5, Colorado > Fort Collins > Carter Lake > Mars Boulder)
> 2. **Mars Traverse** (V4, Colorado > Telluride/Norwood area > Society Turn)
> 3. **Mars Rover** (5.6 Sport, Martian Slabs, Peshastin Pinnacles, Washington)
> 4. **Martian Route** (5.8 Sport, Garden of the Gods, Colorado Springs)

**Sources cited:**
- https://openbeta.io/climb/9aeafe3e-27bb-5b70-9a8f-d39e47198831
- https://www.mountainproject.com/route/119049233/mars-rover

> **Important clarification:** This is NOT a hallucination. Mars Traverse, Mars Rover, and Martian Route are real climbing routes that exist in the database. CruxBot retrieved factually correct information. The issue is **intent misunderstanding** — the system interpreted "Mars" as a keyword search rather than recognizing the question refers to the planet Mars (which is clearly out-of-domain). This is a failure of the domain-check classifier, not of retrieval or generation.

**Human scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 2 | The routes returned are real but answer a different question — user meant the planet Mars, system matched "Mars" as a keyword in route names. |
| Factual Accuracy | 5 | All cited routes genuinely exist in the database — zero fabrication. |
| Citation Quality | 4 | Specific, verifiable OpenBeta and Mountain Project URLs for real routes. |
| Completeness | 1 | Completely misses the actual intent; the correct response would be a refusal or clarification. |
| **Overall** | **3** | Factually accurate retrieval with a complete intent failure — this is a domain detection limitation, not a hallucination. |

> **Note:** Human overall=3 vs GPT-4o=1 — the largest disagreement in the evaluation. GPT-4o scored all 1s following the anti-hallucination rubric rule ("answered instead of refusing = 1"), which does not account for the fact that the retrieved content is factually correct. A human rater distinguishes between fabricated content (true hallucination) and real content returned for the wrong intent (misinterpretation). This reveals a rubric design limitation that a future evaluation should address by separating these two failure modes.

*GPT-4o scores: All dimensions = 1*

---

## Summary Table

| Query | Category | Human Overall | GPT-4o Overall | Difference |
|---|---|---|---|---|
| R01 | Route | 4 | 5 | −1 |
| R03 | Route | 2 | 2 | 0 |
| T09 | Training | 3 | 4 | −1 |
| T01 | Training | 3 | 3 | 0 |
| S07 | Safety | 5 | 5 | 0 |
| S05 | Safety | 2 | 3 | −1 |
| G05 | Gear | 3 | 4 | −1 |
| G01 | Gear | 3 | 3 | 0 |
| H03 | Anti-hallucination | 5 | 5 | 0 |
| H06 | Anti-hallucination | 3 | 1 | +2 |
| **Average** | | **3.3** | **3.5** | **−0.2** |

**Alignment analysis:**
- 5 out of 10 queries: perfect agreement (difference = 0)
- 4 out of 10 queries: human scored 1 point lower than GPT-4o
- 1 out of 10 queries: human scored 1 point higher than GPT-4o (H06)
- Overall alignment is strong, confirming GPT-4o is a reliable automated judge for this task

**Where human and GPT-4o diverged:**
- **R01, T09, G05, S05**: Human penalized more on completeness and citation quality
- **H06 (key disagreement)**: Human scored 2 vs GPT-4o's 1. The routes returned (Mars Traverse, Mars Rover) are real climbing routes in the database — this is a query intent misunderstanding, not a hallucination. GPT-4o's rubric rule ("answered instead of refusing = all 1s") does not distinguish between fabricated content and correctly retrieved content with wrong intent. This reveals a rubric design limitation worth noting in future evaluations.

---

*Note on Citation Quality: Mountain Project forum posts (training and gear categories) do not have specific post-level URLs in the original Kaggle dataset. All 99,173 forum entries share the generic URL `mountainproject.com/forum`. Please consider this data limitation when scoring Citation Quality for T01 and G01.*
