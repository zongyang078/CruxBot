"""
CruxBot Evaluation Visualizer
==============================
Generates two charts from llm_judge_results.json:
  1. Heatmap  — categories × dimensions (for writeup)
  2. Radar    — per-category dimension scores (for slide deck)

Usage:
    python -u scripts/visualize_eval.py

Output:
    evaluation/eval_heatmap.png
    evaluation/eval_radar.png
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

RESULTS_PATH = "evaluation/llm_judge_results.json"

# ── load ──────────────────────────────────────────────────────────────
with open(RESULTS_PATH) as f:
    data = json.load(f)

by_cat = data["by_category"]
overall = data["overall_averages"]

CATEGORIES = ["route", "training", "safety", "gear", "hallucination"]
DIMS       = ["relevance", "factual_accuracy", "citation_quality", "completeness"]
DIM_LABELS = ["Relevance", "Factual\nAccuracy", "Citation\nQuality", "Completeness"]
CAT_LABELS = ["Route", "Training", "Safety", "Gear", "Anti-\nHallucination"]

# matrix: rows = categories, cols = dimensions
matrix = np.array([
    [by_cat[c][d] for d in DIMS]
    for c in CATEGORIES
])

# ══════════════════════════════════════════════════════════════════════
# 1. HEATMAP
# ══════════════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(9, 5))

im = ax.imshow(matrix, cmap="RdYlGn", vmin=1, vmax=5, aspect="auto")

# axis labels
ax.set_xticks(range(len(DIMS)))
ax.set_xticklabels(DIM_LABELS, fontsize=11)
ax.set_yticks(range(len(CATEGORIES)))
ax.set_yticklabels(CAT_LABELS, fontsize=11)

# value annotations
for i in range(len(CATEGORIES)):
    for j in range(len(DIMS)):
        val = matrix[i, j]
        color = "white" if val < 2.5 or val > 4.2 else "black"
        ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                fontsize=13, fontweight="bold", color=color)

# overall column annotation on right side
ax.set_xlim(-0.5, len(DIMS) - 0.5 + 1.2)
for i, c in enumerate(CATEGORIES):
    ov = by_cat[c]["overall"]
    ax.text(len(DIMS) + 0.15, i, f"Overall\n{ov:.1f}/5",
            ha="left", va="center", fontsize=9.5,
            color="#333333", fontweight="bold")

plt.colorbar(im, ax=ax, label="Score (1–5)", shrink=0.85)
ax.set_title("CruxBot GPT-4o Evaluation — Scores by Category & Dimension",
             fontsize=13, fontweight="bold", pad=14)
plt.tight_layout()
os.makedirs("evaluation", exist_ok=True)
plt.savefig("evaluation/eval_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: evaluation/eval_heatmap.png")


# ══════════════════════════════════════════════════════════════════════
# 2. RADAR CHART
# ══════════════════════════════════════════════════════════════════════
RADAR_DIMS       = ["relevance", "factual_accuracy", "citation_quality", "completeness", "overall"]
RADAR_DIM_LABELS = ["Relevance", "Factual\nAccuracy", "Citation\nQuality", "Completeness", "Overall"]
N = len(RADAR_DIMS)

angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
angles += angles[:1]  # close polygon

COLORS = {
    "route":        "#2196F3",
    "training":     "#FF9800",
    "safety":       "#4CAF50",
    "gear":         "#9C27B0",
    "hallucination":"#F44336",
}

fig, ax = plt.subplots(figsize=(8, 7), subplot_kw=dict(polar=True))

for cat, label, color in zip(CATEGORIES, CAT_LABELS, COLORS.values()):
    values = [by_cat[cat][d] for d in RADAR_DIMS]
    values += values[:1]
    ax.plot(angles, values, color=color, linewidth=2, label=label.replace("\n", " "))
    ax.fill(angles, values, color=color, alpha=0.08)

# grid and ticks
ax.set_xticks(angles[:-1])
ax.set_xticklabels(RADAR_DIM_LABELS, fontsize=10.5)
ax.set_yticks([1, 2, 3, 4, 5])
ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=8, color="grey")
ax.set_ylim(0, 5)
ax.spines["polar"].set_visible(False)

ax.set_title("CruxBot GPT-4o Evaluation — Radar by Category",
             fontsize=13, fontweight="bold", pad=20)
ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=10)

plt.tight_layout()
plt.savefig("evaluation/eval_radar.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved: evaluation/eval_radar.png")

print("\nDone! Both charts saved to evaluation/")
