import ctypes, numpy as np, pathlib, random
from pyfastpfor import getCodec          # 의존 해결용

# ── G8CU .so 로드 ───────────────────────────────────────
lib = ctypes.CDLL(str(pathlib.Path("build/libg8cu.so").resolve()))
enc = lib.G8CU_encodeArray32
dec = lib.G8CU_decodeArray32
enc.restype = dec.restype = ctypes.c_size_t
enc.argtypes = [
    ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_uint8)
]
dec.argtypes = [
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t
]

# ── 1)  작은 랜덤 배열로 round-trip 검사 ───────────────
def roundtrip(arr):
    out  = np.empty(arr.size * 5 + 32, dtype=np.uint8)
    back = np.empty_like(arr)
    used = enc(arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
               arr.size,
               out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))
    dec(out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
        back.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
        arr.size)
    idx = np.flatnonzero(arr != back)
    return used, idx, arr, back

#  A) 크기 1~40까지 증가 테스트
for n in range(1, 41):
    a = np.random.randint(0, 2**32-1, n, dtype=np.uint32)
    used, bad, ia, ba = roundtrip(a)
    if bad.size:
        print(f"❌ length {n} – first mismatch at pos {bad[0]}")
        print(" in :", ia[max(0,bad[0]-2):bad[0]+3].tolist())
        print(" out:", ba[max(0,bad[0]-2):bad[0]+3].tolist())
        break
else:
    print("✅ lengths 1–40 all ok")

#  B)  실제 그래프 배열 앞 64개만 확인
import numpy as np, pathlib
sample = np.load(next(pathlib.Path("data").glob("*_dgap.npy")))[:64]
used, bad, ia, ba = roundtrip(sample)
if bad.size:
    print(f"❌ graph sample – first mismatch at {bad[0]}")
else:
    print("✅ graph sample round-trip OK")
