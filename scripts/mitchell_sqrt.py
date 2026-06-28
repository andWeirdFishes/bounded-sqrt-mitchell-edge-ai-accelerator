import numpy as np

def mitchell_sqrt_q1616(raw: int) -> int:
    if raw == 0:
        return 0
    msb = int(np.floor(np.log2(raw)))
    shift = msb // 2 - 8
    if shift >= 0:
        base = raw >> shift
    else:
        base = raw << (-shift)
    if msb % 2 == 1:
        base = base >> 1
    pow2 = 1 << (msb // 2 + 8 + (msb % 2))
    base = (base + pow2) >> 1
    base = base - (base >> 5)
    return base & 0xFFFFFFFF

def mitchell_sqrt_real(x: float) -> float:
    raw = int(x * (1 << 16))
    if raw <= 0:
        return 0.0
    result_raw = mitchell_sqrt_q1616(raw)
    return result_raw / (1 << 16)

def exact_sqrt_real(x: float) -> float:
    return float(np.sqrt(x))