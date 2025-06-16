#!/usr/bin/env python3
"""
메모리 ≤ 300 MB로 수억 간선 엣지리스트 → Δ-gap .npy 를 만드는 스트리밍 버전
"""

import argparse, pathlib, numpy as np

def pass1(path):
    max_node = -1
    edge_cnt = 0
    with open(path) as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip(): continue
            s, d = map(int, ln.split())
            max_node = max(max_node, s, d)
            edge_cnt += 1
    return max_node + 1, edge_cnt

def pass2(path, out_npy, n_nodes, n_edges):
    dgap = np.memmap(out_npy, dtype=np.uint32, mode='w+', shape=(n_edges,))
    idx  = 0
    prev_dst = -1
    curr_src = -1

    with open(path) as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip(): continue
            s, d = map(int, ln.split())

            if s != curr_src:                 # 새로운 src 시작
                curr_src = s
                prev_dst = -1                 # 깜빡이 초기화

            if prev_dst == -1:                # 리스트 첫 원소
                gap = d
            else:
                gap = d - prev_dst
            dgap[idx] = gap
            idx       += 1
            prev_dst   = d
    dgap.flush()
    arr = np.memmap(out_npy, dtype=np.uint32, mode='r', shape=(n_edges,))
    np.save(out_npy, arr)          # 헤더 덮어쓰기

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--txt", required=True, help="edge list txt (src dst per line)")
    ap.add_argument("--out", required=True, help="output .npy path (Δ-gaps)")
    args = ap.parse_args()

    txt = pathlib.Path(args.txt)
    print("⓵  counting …")
    n_nodes, n_edges = pass1(txt)
    print(f"    nodes: {n_nodes:,}  edges: {n_edges:,}")

    print("⓶  streaming Δ-gap → memmap")
    pass2(txt, args.out, n_nodes, n_edges)
    
    print(f"[saved] {args.out}")

if __name__ == "__main__":
    main()
