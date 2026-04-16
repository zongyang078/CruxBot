# CruxBot Human Evaluation — 10 Representative Queries

**Purpose:** Validate the GPT-4o automated evaluation by comparing human scores against LLM scores on 10 representative queries (2 per category).

**Instructions:**
- Read each query and CruxBot's answer carefully
- Score on 4 dimensions using the rubric below (1–5)
- Write a brief reason (1 sentence) for each score
- Do NOT look at the GPT-4o scores until you have finished

**Rater name:** _______________
**Date:** _______________

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance |5 | Answers the query with the desired information.|
| Factual Accuracy |5 |Both are real routes that correspond to the climbing rating. |
| Citation Quality |5 |Specific clickable URLs |
| Completeness |3 |The only constraint is California, but the answer only provides options in Castle Crags. Many other options exist in California matching this criteria that could've been included. |
| **Overall** |4 |Factual and relevant information. Lacking in completeness. |

*GPT-4o scores (fill in after): Relevance=5, Accuracy=5, Citation=4, Completeness=5, Overall=5*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 3| The query asks for V4 bouldering routes in Bishop, CA, but the answers include Bishop Peak (San Luis Obispo, CA). There are many famous V4 problems in Bishop that were not listed.|
| Factual Accuracy | 3| Bishop Peak and Bishop, CA are quite far from each other. Mammoth Lakes is not in Bishop, but it appears that they are often grouped together. Volanic Tablelands is correct.|
| Citation Quality | 2|Citations are not to problems in Bishop. |
| Completeness | 2| Many famous V4's in Bishop that are not included. |
| **Overall** | 2| Does not answer the query effectively.|

*GPT-4o scores (fill in after): Relevance=3, Accuracy=2, Citation=2, Completeness=2, Overall=2*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5| Answers the query. |
| Factual Accuracy | 4|These are verifiably things that can improve climbing ability regardless of the plateau mentioned. |
| Citation Quality | 1| No specific URLs|
| Completeness | 2| Addresses some options, but doesn't give actionable advice, such as improving finger strength, cleaning up footwork, etc.|
| **Overall** | 2| Relevant, but very shallow information.|

*GPT-4o scores (fill in after): Relevance=5, Accuracy=4, Citation=3, Completeness=4, Overall=4*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5|Answers the query. |
| Factual Accuracy | 5| Hangboards with soft rounded edges are useful for sloper strength due to their lack of friction.|
| Citation Quality | 3| 1 specific and 1 generic URL|
| Completeness | 3| Provides an actionable starting point, but there is much more to do for training finger strength.|
| **Overall** | 4|Relevant and useful information, but missing completeness. |

*GPT-4o scores (fill in after): Relevance=5, Accuracy=3, Citation=1, Completeness=4, Overall=3*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5| Directly answers the query.|
| Factual Accuracy | 5| The list is fully accurate.|
| Citation Quality | 5| Specific and relevant URLs|
| Completeness | 5| Comprehensive answer.|
| **Overall** | 5| Fulfills all criteria completely. |

*GPT-4o scores (fill in after): Relevance=5, Accuracy=5, Citation=5, Completeness=5, Overall=5*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 2| Mentions there is no accident information, but doesn't attempt to retrieve relevant information i.e. Red River Gorge information.|
| Factual Accuracy | 5| No hallucination/fabrication with accurate safety information.|
| Citation Quality | 2|Usable and specific URLs for routes in Red River Gorge, but information is not mentioned in the answer. |
| Completeness | 1| Doesn't answer the question and doesn't mention any information about Red River Gorge beyond generic safety information. |
| **Overall** | 2|Accurate but irrelevant answer. |

*GPT-4o scores (fill in after): Relevance=3, Accuracy=5, Citation=1, Completeness=2, Overall=3*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5| Answers the query. |
| Factual Accuracy | 5| Rating and description correct and attributed to Trailspace. |
| Citation Quality | 1| Non-specific URL |
| Completeness | 2| Missing many parameters. |
| **Overall** | 3| Relevant and accurate, but citation is not good and many parameters are missing. |

*GPT-4o scores (fill in after): Relevance=5, Accuracy=3, Citation=3, Completeness=4, Overall=4*

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

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5| Answers the query. |
| Factual Accuracy | 4| Can't verify Mammut Bionic has lowest friction.|
| Citation Quality | 1| Non-specific URLs |
| Completeness | 3| Valid options, but no comparison information and missing many parameters|
| **Overall** | 3| Answers the query, but without depth. |

*GPT-4o scores (fill in after): Relevance=5, Accuracy=3, Citation=1, Completeness=4, Overall=3*

---

## Category 5: Anti-Hallucination

### H03 — Correct refusal (expected: all 5s)
**Query:** How do I fix a bug in my Python code?

**CruxBot Answer:**
> I don't have data on this in my climbing knowledge base. I can only answer questions about rock climbing.

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 5| Correctly says it's out of scope. |
| Factual Accuracy | 5| Correct refusal. |
| Citation Quality | 5| No citation. |
| Completeness | 5| Refual is accurate/complete.|
| **Overall** | 5| Correct response. |

*GPT-4o scores (fill in after): All dimensions = 5*

---

### H06 — Failed refusal (expected: all 1s)
**Query:** What climbing routes are on Mars?

**CruxBot Answer:**
> Based on the provided context, I found several routes related to "Mars":
>
> 1. **Mars Traverse** (V5, Colorado > Fort Collins > Carter Lake > Mars Boulder)
> 2. **Mars Traverse** (V4, Colorado > Telluride/Norwood area > Society Turn)
> 3. **Mars Rover** (5.6 Sport, Martian Slabs, Peshastin Pinnacles, Washington)
> 4. **Martian Route** (5.8 Sport, Garden of the Gods, Colorado Springs)
>
> *(CruxBot misinterpreted "Mars" as a keyword and returned Earth routes with "Mars" in the name — should have refused.)*

**Sources cited:**
- https://openbeta.io/climb/9aeafe3e-27bb-5b70-9a8f-d39e47198831
- https://www.mountainproject.com/route/119049233/mars-rover

**Your scores:**

| Dimension | Score (1–5) | Reason |
|---|---|---|
| Relevance | 2| Although the implicit intent of the query was to ask about the planet, the answers are about climibing routes on Mars.|
| Factual Accuracy | 5| All routes exist and match the query. |
| Citation Quality | 5| Specific URLs |
| Completeness | 1| Should've asked for clarification i.e. did you mean Mars Traverse? |
| **Overall** | 3| Accurate information, but shouldn't necessarily have answered this way. |

*GPT-4o scores (fill in after): All dimensions = 1*

---

## Summary Table (fill in after completing all queries)

| Query | Category | Your Overall | GPT-4o Overall | Difference |
|---|---|---|---|---|
| R01 | Route | 4| 5 | -1|
| R03 | Route | 2| 2 | 0|
| T09 | Training | 2| 4 | -2|
| T01 | Training | 4| 3 | 1|
| S07 | Safety | 5| 5 | 0|
| S05 | Safety | 2| 3 | -1|
| G05 | Gear | 3| 4 | -1|
| G01 | Gear | 3| 3 | 0|
| H03 | Anti-hallucination | 5| 5 | 0|
| H06 | Anti-hallucination | 3| 1 |2 |
| **Average** | | 3.3| **3.50** | -0.2|

---

*Note on Citation Quality: Mountain Project forum posts (training and gear categories) do not have specific post-level URLs in the original Kaggle dataset. All 99,173 forum entries share the generic URL `mountainproject.com/forum`. Please consider this data limitation when scoring Citation Quality for T01 and G01.*
