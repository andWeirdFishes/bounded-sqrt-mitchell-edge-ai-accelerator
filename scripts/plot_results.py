import numpy as np
import matplotlib.pyplot as plt
import csv
from pathlib import Path

SIM_DIR = Path(__file__).resolve().parent.parent / "sim"

def load_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

retrieval = load_csv(SIM_DIR / "cosine_retrieval_results.csv")
threshold = load_csv(SIM_DIR / "cosine_threshold_results.csv")

TASK_COLORS = {
    "speaker_verification": "#4C9BE8",
    "semantic_retrieval":   "#6DBF6A",
    "anomaly_detection":    "#E8874C",
}
TASK_LABELS = {
    "speaker_verification": "Speaker Verif.",
    "semantic_retrieval":   "Semantic Retr.",
    "anomaly_detection":    "Anomaly Det.",
}

fig, axes = plt.subplots(3, 1, figsize=(8,16))
fig.suptitle("Mitchell Approximation: Cosine Similarity Accuracy Across Tasks", fontsize=13, fontweight="bold")

ax = axes[0]
for task, color in TASK_COLORS.items():
    rows = [r for r in retrieval if r["task"] == task]
    dims = sorted(set(int(r["dim"]) for r in rows))
    for dim in dims:
        dim_rows = [r for r in rows if int(r["dim"]) == dim]
        ks = [int(r["n_classes"]) for r in dim_rows]
        maes = [float(r["mean_abs_cosine_err"]) for r in dim_rows]
        ax.plot(ks, maes, marker="o", color=color, alpha=0.5, linewidth=1, markersize=4)
    agg_by_k = {}
    for r in rows:
        k = int(r["n_classes"])
        agg_by_k.setdefault(k, []).append(float(r["mean_abs_cosine_err"]))
    ks_agg = sorted(agg_by_k.keys())
    maes_agg = [np.mean(agg_by_k[k]) for k in ks_agg]
    ax.plot(ks_agg, maes_agg, marker="o", color=color, linewidth=2.5, markersize=6, label=TASK_LABELS[task])

ax.set_xlabel("Number of Classes K")
ax.set_ylabel("Mean |Δcos| (absolute cosine error)")
ax.set_title("Cosine Error vs Classes")
ax.legend(fontsize=8)
ax.set_xscale("log")
ax.grid(True, ls="--", alpha=0.4)

ax = axes[1]
for task, color in TASK_COLORS.items():
    rows = [r for r in retrieval if r["task"] == task]
    all_dims = sorted(set(int(r["dim"]) for r in rows))
    agg_by_dim = {}
    for r in rows:
        d = int(r["dim"])
        agg_by_dim.setdefault(d, []).append(float(r["mean_abs_cosine_err"]))
    dims_agg = sorted(agg_by_dim.keys())
    maes_agg = [np.mean(agg_by_dim[d]) for d in dims_agg]
    ax.plot(dims_agg, maes_agg, marker="s", color=color, linewidth=2.5, markersize=6, label=TASK_LABELS[task])

bound_x = np.linspace(32, 768, 200)
bound_y = 1/32 * np.ones_like(bound_x)
ax.plot(bound_x, bound_y, "k--", linewidth=1.5, label="Theoretical bound (1/32)")

ax.set_xlabel("Embedding Dimension D")
ax.set_ylabel("Mean |Δcos|")
ax.set_title("Cosine Error vs Dimension")
ax.legend(fontsize=8)
ax.set_xscale("log")
ax.grid(True, ls="--", alpha=0.4)

ax = axes[2]
task_names_plot = ["speaker_verification", "anomaly_detection"]
task_labels_plot = [TASK_LABELS[t] for t in task_names_plot]
x = np.arange(len(task_names_plot))
w = 0.35

for i, task in enumerate(task_names_plot):
    rows = [r for r in threshold if r["task"] == task]
    vr_vals = [float(r["violation_rate"]) for r in rows]
    sr_vals = [float(r["safe_rate_with_margin"]) for r in rows]
    mean_vr = np.mean(vr_vals)
    mean_sr = np.mean(sr_vals)
    ax.bar(i - w/2, mean_vr * 100, w, color=TASK_COLORS[task], alpha=0.7, label=f"{TASK_LABELS[task]} tight viol.")
    ax.bar(i + w/2, (1 - mean_sr) * 100, w, color=TASK_COLORS[task], alpha=0.3, label=f"{TASK_LABELS[task]} margin viol.")

ax.set_xticks(x)
ax.set_xticklabels(task_labels_plot, fontsize=9)
ax.set_ylabel("Decision Violation Rate (%)")
ax.set_title(f"Threshold Violations (τ=0.75, margin=1/32)")
ax.legend(fontsize=7)
ax.grid(True, ls="--", alpha=0.4, axis="y")

plt.tight_layout()
plt.savefig(SIM_DIR / "cosine_accuracy_results.png", dpi=150)
print(f"Saved -> sim/cosine_accuracy_results.png")

fig2, ax2 = plt.subplots(figsize=(7, 5))
ax2.set_title("Top-1 Rank Preservation: Mitchell Approx vs Exact", fontsize=12, fontweight="bold")

for task, color in TASK_COLORS.items():
    rows = [r for r in retrieval if r["task"] == task]
    dims = sorted(set(int(r["dim"]) for r in rows))
    for dim in dims:
        dim_rows = sorted([r for r in rows if int(r["dim"]) == dim], key=lambda r: int(r["n_classes"]))
        ks = [int(r["n_classes"]) for r in dim_rows]
        t1s = [float(r["recall@1"]) for r in dim_rows]
        ax2.plot(ks, t1s, marker="o", color=color, alpha=0.6, linewidth=1, markersize=4)

from matplotlib.lines import Line2D
legend_elements = [Line2D([0], [0], color=c, linewidth=2, label=TASK_LABELS[t]) for t, c in TASK_COLORS.items()]
ax2.legend(handles=legend_elements, fontsize=9)
ax2.set_xlabel("Number of Classes K")
ax2.set_ylabel("Top-1 Preservation Rate")
ax2.set_ylim(0.95, 1.005)
ax2.axhline(1.0, color="black", linestyle="--", linewidth=1.5, alpha=0.7, label="Perfect preservation")
ax2.set_xscale("log")
ax2.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.savefig(SIM_DIR / "top1_preservation.png", dpi=150)
print(f"Saved -> sim/top1_preservation.png")

fig3, axes3 = plt.subplots(3, 1, figsize=(8,16))
fig3.suptitle("Recall@K Preservation: Mitchell Approx vs Exact", fontsize=13, fontweight="bold")

TOPK = [1, 5, 10, 30]
task_list = ["speaker_verification", "semantic_retrieval", "anomaly_detection"]

for ax_idx, task in enumerate(task_list):
    ax = axes3[ax_idx]
    rows = [r for r in retrieval if r["task"] == task]
    dims = sorted(set(int(r["dim"]) for r in rows))
    cmap = plt.cm.viridis(np.linspace(0.1, 0.9, len(dims)))

    for di, dim in enumerate(dims):
        dim_rows = sorted([r for r in rows if int(r["dim"]) == dim], key=lambda r: int(r["n_classes"]))
        ks_plot = sorted(set(int(r["n_classes"]) for r in dim_rows))

        for kv in TOPK:
            key = f"recall@{kv}"
            if key not in dim_rows[0]:
                continue
            vals = [float(r[key]) for r in dim_rows]
            ax.plot(ks_plot, vals, marker="o", color=cmap[di],
                    linestyle=["-","--",":","-."][TOPK.index(kv)],
                    linewidth=1.5, markersize=4, alpha=0.8)

    from matplotlib.lines import Line2D
    style_legend = [Line2D([0],[0], color="gray", linestyle=ls, label=f"recall@{kv}")
                    for kv, ls in zip(TOPK, ["-","--",":","-."])]
    dim_legend = [Line2D([0],[0], color=cmap[di], linewidth=2, label=f"D={dim}")
                  for di, dim in enumerate(dims)]
    ax.legend(handles=style_legend + dim_legend, fontsize=6, ncol=2)
    ax.set_xlabel("Number of Classes K")
    ax.set_ylabel("Recall@K")
    ax.set_title(TASK_LABELS[task])
    ax.set_xscale("log")
    ax.set_ylim(0.998, 1.0005)
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, alpha=0.5)
    ax.grid(True, ls="--", alpha=0.4)

plt.tight_layout()
plt.savefig(SIM_DIR / "recallk_results.png", dpi=150)
print(f"Saved -> sim/recallk_results.png")