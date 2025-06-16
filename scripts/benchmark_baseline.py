#!/usr/bin/env python3
"""
Benchmark Δ-gap codecs.

• pyfastpfor  : any codec returned by getCodec()  (default: streamvbyte)
• g8cu        : our AVX2 G8CU implementation (build/libg8cu.so)

Examples
--------
# 기본(streamvbyte) 실행
python benchmark_baseline.py

# fastpfor256 실행
python benchmark_baseline.py --codec fastpfor256

# g8cu 실행
python benchmark_baseline.py --codec g8cu
"""

import argparse, ctypes, os, pathlib, time
import numpy as np, pandas as pd
from pyfastpfor import getCodec, getCodecList

DATA_DIR    = pathlib.Path("data")       # *_dgap.npy 위치
RESULTS_DIR = pathlib.Path("results"); RESULTS_DIR.mkdir(exist_ok=True)

# ──────────────────────────────────────────────────────────────
def load_g8cu():
    so_path = pathlib.Path("build/libg8cu.so")
    if not so_path.exists():
        raise SystemExit("❌ build/libg8cu.so 가 없습니다. 먼저 컴파일하세요.")
    lib = ctypes.CDLL(str(so_path.resolve()))

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
    return enc, dec
# ──────────────────────────────────────────────────────────────
def load_g8cu_nib():
    so_path = pathlib.Path("build/libg8cu_nib.so")
    if not so_path.exists():
        raise SystemExit("❌ build/libg8cu_nib.so 가 없습니다. 먼저 컴파일하세요.")
    lib = ctypes.CDLL(str(so_path.resolve()))

    enc = lib.G8CU_NIB_encodeArray32
    dec = lib.G8CU_NIB_decodeArray32

    enc.restype = dec.restype = ctypes.c_size_t
    enc.argtypes = [
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8)
    ]
    dec.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t
    ]
    return enc, dec

def load_g8cu_fast():
    so = pathlib.Path("build/libg8cu_fast.so")
    if not so.exists(): raise SystemExit("build/libg8cu_fast.so가 없습니다.")
    lib = ctypes.CDLL(str(so.resolve()))
    enc, dec = lib.G8CU_FAST_encodeArray32, lib.G8CU_FAST_decodeArray32
    enc.restype = dec.restype = ctypes.c_size_t
    enc.argtypes = [
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8)]
    dec.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t]
    return enc, dec

# ❶ loader 추가
def load_g8cu_fp():
    so = pathlib.Path("build/libg8cu_fp.so")
    if not so.exists():
        raise SystemExit("❌ build/libg8cu_fp.so 가 없습니다.")
    lib = ctypes.CDLL(str(so.resolve()))
    enc, dec = lib.G8CU_FP_encodeArray32, lib.G8CU_FP_decodeArray32
    enc.restype = dec.restype = ctypes.c_size_t
    enc.argtypes = [
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_uint8)]
    dec.argtypes = [
        ctypes.POINTER(ctypes.c_uint8),
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_size_t]
    return enc, dec

# ──────────────────────────────────────────────────────────────
def bench_pyfastpfor(arr: np.ndarray, codec):
    out  = np.empty(arr.size * 3, dtype=np.uint32)
    back = np.empty_like(arr)

    t0   = time.perf_counter()
    used = codec.encodeArray(arr, arr.size, out, out.size)
    enc_t = time.perf_counter() - t0

    t0 = time.perf_counter()
    codec.decodeArray(out, arr.size, back, back.size)
    dec_t = time.perf_counter() - t0

    assert np.array_equal(arr, back)
    mb = arr.nbytes / 1e6
    return mb/enc_t, mb/dec_t, used*32/arr.size
# ──────────────────────────────────────────────────────────────
def bench_g8cu(arr: np.ndarray, encode_u8, decode_u8):
    n     = arr.size
    out   = np.empty(n * 5 + 32, dtype=np.uint8)   # 여유 32 B
    back  = np.empty_like(arr)

    t0 = time.perf_counter()
    used = encode_u8(arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
                     n,
                     out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))
    enc_t = time.perf_counter() - t0

    t0 = time.perf_counter()
    decode_u8(out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
              back.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32)),
              n)
    dec_t = time.perf_counter() - t0

    assert np.array_equal(arr, back)        # ← 패딩 필요 없음
    mb = arr.nbytes / 1e6
    return mb/enc_t, mb/dec_t, used*8/n     # used = byte, 8 bit/edge


# ──────────────────────────────────────────────────────────────
def main(codec_name: str):
    codec_name = codec_name.lower()
    rows = []

    if codec_name == "g8cu":
        encode_u8, decode_u8 = load_g8cu()
        codec = None
    elif codec_name == "g8cu-nib":
        encode_u8, decode_u8 = load_g8cu_nib()
        codec = None
    elif codec_name == "g8cu-fast":
        encode_u8, decode_u8 = load_g8cu_fast()
        codec = None
    elif codec_name == "g8cu-fp":
        encode_u8, decode_u8 = load_g8cu_fp()
    else:
        if codec_name not in getCodecList():
            raise SystemExit(f"codec '{codec_name}' not found "
                             f"(choices: g8cu, {', '.join(getCodecList())})")
        codec = getCodec(codec_name)

    for npy in sorted(DATA_DIR.glob("*_dgap.npy")):
        graph = npy.stem.split("_")[0]
        arr   = np.load(npy)

        if codec_name == "g8cu":
            enc, dec, bpe = bench_g8cu(arr, encode_u8, decode_u8)
        elif codec_name == "g8cu-nib":
            enc, dec, bpe = bench_g8cu(arr, encode_u8, decode_u8)
        elif codec_name == "g8cu-fast":
            enc, dec, bpe = bench_g8cu(arr, encode_u8, decode_u8)
        if codec_name in ("g8cu", "g8cu-fp"):
            enc, dec, bpe = bench_g8cu(arr, encode_u8, decode_u8)
        else:
            enc, dec, bpe = bench_pyfastpfor(arr, codec)

        rows.append((graph, enc, dec, bpe))
        print(f"[{graph:12}] enc {enc:7.1f} MB/s  "
              f"dec {dec:7.1f} MB/s  bpe {bpe:5.2f}")

    df = pd.DataFrame(rows, columns=["graph", "enc_MBps", "dec_MBps", "bpe"])
    out = RESULTS_DIR / f"{codec_name}.csv"
    df.to_csv(out, index=False)
    print("\nSaved:", out)

# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--codec", default="streamvbyte",
                    help="streamvbyte (default), fastpfor256, g8cu, g8cu-nib")
    main(ap.parse_args().codec)
