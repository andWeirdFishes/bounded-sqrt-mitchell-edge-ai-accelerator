import numpy as np
import csv
from pathlib import Path
from mitchell_sqrt import mitchell_sqrt_real

RNG = np.random.default_rng(42)

TOPK_VALUES = [1, 5, 10, 30]
CHUNK = 512
MAX_N = 3000

TASKS = {
    "speaker_verification": {
        "dims": [256, 512],
        "n_classes": [10, 50, 100, 500, 1000],
        "n_per_class": 30,
    },
    "semantic_retrieval": {
        "dims": [32, 64, 128, 384, 768],
        "n_classes": [10, 50, 100, 500, 1000],
        "n_per_class": 20,
    },
    "anomaly_detection": {
        "dims": [32, 64, 128],
        "n_classes": [10, 50, 100],
        "n_per_class": 50,
    },
}

MARGIN = np.float32(1.0 / 32.0)
THRESHOLD = np.float32(0.75)

def mitchell_sqrt_vec(x_arr: np.ndarray) -> np.ndarray:
    out = np.zeros(len(x_arr), dtype=np.float32)
    for i, x in enumerate(x_arr):
        out[i] = mitchell_sqrt_real(float(x))
    return out

def make_embeddings(dim: int, n_classes: int, n_per_class: int):
    n = n_classes * n_per_class
    centers = RNG.standard_normal((n_classes, dim)).astype(np.float32)
    centers /= np.linalg.norm(centers, axis=1, keepdims=True)
    noise = RNG.standard_normal((n, dim)).astype(np.float32) * 0.3
    labels = np.repeat(np.arange(n_classes), n_per_class)
    raw = centers[labels] + noise
    raw /= np.linalg.norm(raw, axis=1, keepdims=True)
    return raw, labels

def normalize_approx(E: np.ndarray) -> np.ndarray:
    sq = np.sum(E.astype(np.float64) ** 2, axis=1)
    an = mitchell_sqrt_vec(sq)
    an = np.where(an < 1e-12, np.float32(1e-12), an)
    return (E / an[:, None]).astype(np.float32)

def topk_pass(En: np.ndarray, kk: int) -> np.ndarray:
    n = En.shape[0]
    out = np.empty((n, kk), dtype=np.int32)
    for start in range(0, n, CHUNK):
        end = min(start + CHUNK, n)
        row = (En[start:end] @ En.T).astype(np.float32)
        row[:, start:end].flat[:: end - start + 1] = np.float32(-2.0)
        part = np.argpartition(row, -kk, axis=1)[:, -kk:]
        vals = row[np.arange(end - start)[:, None], part]
        order = np.argsort(-vals, axis=1)
        out[start:end] = part[np.arange(end - start)[:, None], order]
    return out

def run_config(E: np.ndarray, do_threshold: bool):
    n = E.shape[0]
    En_e = E.copy()
    En_a = normalize_approx(E)

    KK = max(TOPK_VALUES) + 1
    tk_e = topk_pass(En_e, KK)
    tk_a = topk_pass(En_a, KK)

    recall, exact_match = {}, {}
    for kv in TOPK_VALUES:
        if kv >= n:
            continue
        sets_e = [frozenset(tk_e[i, :kv]) for i in range(n)]
        sets_a = [frozenset(tk_a[i, :kv]) for i in range(n)]
        recall[kv] = float(np.mean([len(sets_e[i] & sets_a[i]) / kv for i in range(n)]))
        exact_match[kv] = float(np.mean([sets_e[i] == sets_a[i] for i in range(n)]))

    mae_sum = np.float64(0.0)
    max_err = np.float32(0.0)
    n_cells = 0
    viol = 0
    margin_viol = 0
    thresh_pairs = 0

    for start in range(0, n, CHUNK):
        end = min(start + CHUNK, n)
        se = (En_e[start:end] @ En_e.T).astype(np.float32)
        sa = (En_a[start:end] @ En_a.T).astype(np.float32)
        se[:, start:end].flat[:: end - start + 1] = np.float32(0.0)
        sa[:, start:end].flat[:: end - start + 1] = np.float32(0.0)
        ae = np.abs(se - sa)
        mae_sum += float(ae.sum())
        cur_max = float(ae.max())
        if cur_max > max_err:
            max_err = cur_max
        n_cells += ae.size

        if do_threshold:
            row_idx = np.arange(start, end)
            col_mask = np.arange(n)[None, :] > row_idx[:, None]
            mm = (se >= THRESHOLD) != (sa >= THRESHOLD)
            mm_triu = mm & col_mask
            viol += int(mm_triu.sum())
            margin_viol += int((mm_triu & (np.abs(se - THRESHOLD) < MARGIN)).sum())
            thresh_pairs += int(col_mask.sum())

    mae = float(mae_sum / n_cells)
    thr_out = None
    if do_threshold and thresh_pairs > 0:
        thr_out = (
            float(viol / thresh_pairs),
            float(1.0 - margin_viol / thresh_pairs),
            thresh_pairs,
        )

    return recall, exact_match, mae, float(max_err), thr_out

SIM_DIR = Path(__file__).resolve().parent.parent / "sim"
SIM_DIR.mkdir(exist_ok=True)

retrieval_rows = []
threshold_rows = []

for task_name, cfg in TASKS.items():
    print(f"\n{task_name}")
    do_thr = task_name in ("speaker_verification", "anomaly_detection")
    for dim in cfg["dims"]:
        for k in cfg["n_classes"]:
            n_per = cfg["n_per_class"]
            n_total = k * n_per
            if n_total > MAX_N:
                n_per_actual = max(2, MAX_N // k)
            else:
                n_per_actual = n_per

            E, labels = make_embeddings(dim, k, n_per_actual)
            n = len(E)

            recall, exact_match, mae, maxe, thr = run_config(E, do_thr)

            row = {
                "task": task_name, "dim": dim, "n_classes": k,
                "n_per_class": n_per_actual, "n_total": n,
            }
            for kv in TOPK_VALUES:
                if kv in recall:
                    row[f"recall@{kv}"] = round(recall[kv], 6)
                    row[f"exact_match@{kv}"] = round(exact_match[kv], 6)
            row["mean_abs_cosine_err"] = round(mae, 8)
            row["max_abs_cosine_err"] = round(maxe, 8)
            retrieval_rows.append(row)

            summary = " ".join([f"rec@{kv}={recall[kv]:.4f}" for kv in TOPK_VALUES if kv in recall])
            print(f"  D={dim} K={k} n={n}: {summary}  mae={mae:.5f}")

            if thr is not None:
                vr, sr, npairs = thr
                threshold_rows.append({
                    "task": task_name, "dim": dim, "n_classes": k,
                    "n_per_class": n_per_actual, "n_total": n,
                    "threshold": float(THRESHOLD), "margin": float(MARGIN),
                    "violation_rate": round(vr, 6),
                    "safe_rate_with_margin": round(sr, 6),
                    "total_pairs": npairs,
                })

with open(SIM_DIR / "cosine_retrieval_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=retrieval_rows[0].keys())
    w.writeheader()
    w.writerows(retrieval_rows)

with open(SIM_DIR / "cosine_threshold_results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=threshold_rows[0].keys())
    w.writeheader()
    w.writerows(threshold_rows)

print(f"\n{'='*50}")
for kv in TOPK_VALUES:
    key = f"recall@{kv}"
    vals = [float(r[key]) for r in retrieval_rows if key in r]
    if vals:
        perfect = all(v == 1.0 for v in vals)
        print(f"Min recall@{kv}: {min(vals):.6f}  perfect: {perfect}")