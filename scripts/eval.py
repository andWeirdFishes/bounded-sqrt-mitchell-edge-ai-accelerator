import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import csv

BASE: Path = Path(__file__).resolve().parent.parent / "sim"

FILES: dict[str, str] = {
    "standard": "output_standard.txt",
    "lossy":    "output_lossy.txt",
}

CYCLES: dict[str, int] = {
    "standard": 25,
    "lossy":    2,
}

COLORS: dict[str, str] = {
    "standard": "#4C9BE8",
    "lossy":    "#6DBF6A",
}

EPS: float = 1e-12

def load(path: Path) -> np.ndarray:
    if not path.exists():
        print(f"Warning: {path} not found.")
        return np.array([])
    with open(path, "r") as f:
        return np.array([float(x.strip()) for x in f if x.strip()])

def calculate_metrics(pred_real: np.ndarray, true_real: np.ndarray) -> dict:
    err = pred_real - true_real
    abs_err = np.abs(err)
    rel_err = abs_err / (true_real + EPS)
    max_idx = int(np.argmax(rel_err))
    return {
        "mse":         float(np.mean(err ** 2)),
        "mae":         float(np.mean(abs_err)),
        "max_err":     float(np.max(abs_err)),
        "rel_mae":     float(np.mean(rel_err) * 100),
        "max_rel_err": float(np.max(rel_err) * 100),
        "max_idx":     max_idx,
    }

gold_raw: np.ndarray = load(BASE / "golden_ref.txt")
gold_real: np.ndarray = gold_raw / (1 << 16)

results: list = []
for name, filename in FILES.items():
    pred_raw = load(BASE / filename)
    if len(pred_raw) == 0:
        continue
    n = min(len(pred_raw), len(gold_real))
    pred_real = pred_raw[:n] / (1 << 16)
    true_real = gold_real[:n]
    m = calculate_metrics(pred_real, true_real)
    idx = m["max_idx"]
    worst_true = true_real[idx]
    worst_pred = pred_real[idx]
    worst_abs  = abs(worst_pred - worst_true)
    worst_rel  = worst_abs / (worst_true + EPS) * 100
    x_input = gold_raw[idx]
    speed = 1.0 / CYCLES[name]
    results.append((name, m, speed))
    print(f"\n{'='*44}")
    print(f"  {name.upper()}")
    print(f"{'='*44}")
    print(f"  MAE:             {m['mae']:.8f}")
    print(f"  Max error:       {m['max_err']:.8f}")
    print(f"  Relative MAE:    {m['rel_mae']:.4f}%")
    print(f"  Max rel error:   {m['max_rel_err']:.4f}%")
    print(f"  MSE:             {m['mse']:.4e}")
    print(f"  Throughput:      1/{CYCLES[name]} = {speed:.5f}")
    print(f"\n  --- Worst Relative Error Case ---")
    print(f"  Input (raw Q16.16): {int(x_input)}")
    print(f"  Input (real):       {x_input / (1 << 16):.6f}")
    print(f"  True sqrt:          {worst_true:.6f}")
    print(f"  Predicted sqrt:     {worst_pred:.6f}")
    print(f"  Abs error:          {worst_abs:.6f}")
    print(f"  Rel error:          {worst_rel:.4f}%")

csv_path: Path = BASE / "results.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "model", "mae_real", "max_error_real", "rel_mae_pct",
        "max_rel_error_pct", "mse_real", "cycles", "speed"
    ])
    for name, m, speed in results:
        writer.writerow([
            name,
            f"{m['mae']:.8f}",
            f"{m['max_err']:.8f}",
            f"{m['rel_mae']:.6f}",
            f"{m['max_rel_err']:.6f}",
            f"{m['mse']:.4e}",
            CYCLES[name],
            f"{speed:.6f}",
        ])

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Square Root Implementations: Accuracy vs Speed", fontsize=14, fontweight="bold")
ax1 = axes[0]
for name, m, speed in results:
    ax1.scatter(speed, m["mae"], s=150, color=COLORS[name], zorder=5,
                label=f"{name.upper()}  MAE={m['mae']:.2e}")
ax1.set_yscale("log")
ax1.set_xlabel("Throughput (1 / cycles per sample)")
ax1.set_ylabel("MAE — real units (log scale)")
ax1.set_title("MAE vs Throughput")
ax1.legend(fontsize=8)
ax1.grid(True, which="both", ls="--", alpha=0.4)
ax2 = axes[1]
names_list = [r[0].upper() for r in results]
max_rel = [r[1]["max_rel_err"] for r in results]
rel_mae = [r[1]["rel_mae"] for r in results]
x = np.arange(len(names_list))
w = 0.35
ax2.bar(x - w/2, rel_mae, w, label="Rel MAE (%)")
ax2.bar(x + w/2, max_rel, w, label="Max Rel Error (%)")
ax2.set_xticks(x)
ax2.set_xticklabels(names_list)
ax2.set_ylabel("Relative Error (%)")
ax2.set_title("Relative Error Comparison")
ax2.legend()
ax2.grid(True, ls="--", alpha=0.4)
plt.tight_layout()
plt.savefig(BASE / "accuracy_vs_speed.png", dpi=150)