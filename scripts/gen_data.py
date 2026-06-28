import numpy as np
from pathlib import Path

N = 1000

SCRIPT_DIR = Path(__file__).resolve().parent
SIM_DIR = SCRIPT_DIR.parent / "sim"

INPUT_FILE = SIM_DIR / "input_data.txt"
GOLD_FILE = SIM_DIR / "golden_ref.txt"

def float_to_q16(x):
    return int(x * (1 << 16))

inputs = np.random.randint(1, 2**32 - 1, size=N, dtype=np.uint32)

gold = np.sqrt(inputs.astype(np.float64) / (1 << 16))

with open(INPUT_FILE, "w") as f:
    for x in inputs:
        f.write(f"{int(x):08X}\n")

with open(GOLD_FILE, "w") as f:
    for g in gold:
        f.write(f"{float_to_q16(g)}\n")

print("Generated:")
print(INPUT_FILE)
print(GOLD_FILE)