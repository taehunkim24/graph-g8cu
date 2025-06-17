#!/usr/bin/env python3
"""
prep_graph.py  ── 그래프(엣지리스트) → Δ-gap numpy 배열 변환 스크립트
────────────────────────────────────────────────────────────────────
사용 예
------

# 1) 공개 URL 자동 다운로드 & 변환
python prep_graph.py --name youtube

# 2) 이미 추출된 TXT 엣지리스트 사용
python prep_graph.py --name uk2002 --raw data/uk-2002.txt
"""

import argparse, pathlib, gzip, urllib.request, shutil
import numpy as np

DATA_DIR = pathlib.Path("data")
DATA_DIR.mkdir(exist_ok=True)

URLS = {
    "youtube"     : "https://snap.stanford.edu/data/bigdata/communities/com-youtube.ungraph.txt.gz",
    "dblp"        : "https://snap.stanford.edu/data/bigdata/communities/com-dblp.ungraph.txt.gz", 
    "livejournal" : "https://snap.stanford.edu/data/soc-LiveJournal1.txt.gz",
    "soc-pokec"   : "https://snap.stanford.edu/data/soc-pokec-relationships.txt.gz",
    "twitter"     : "https://snap.stanford.edu/data/twitter-2010.txt.gz",
    "google"      : "https://snap.stanford.edu/data/web-Google.txt.gz",
    # uk2002
}

def download(url: str, out: pathlib.Path):
    if out.exists():
        print(f"[skip] {out.name} already exists")
        return out
    print(f"[download] {url} → {out.name}")
    with urllib.request.urlopen(url) as r, open(out, 'wb') as f:
        shutil.copyfileobj(r, f)
    return out

def ensure_txt(name: str) -> pathlib.Path:
    url = URLS[name]
    gz_path = DATA_DIR / pathlib.Path(url).name
    download(url, gz_path)
    if gz_path.suffix == '.gz':
        txt_path = gz_path.with_suffix('')
        if not txt_path.exists():
            print(f"[gunzip] {gz_path.name} → {txt_path.name}")
            with gzip.open(gz_path, 'rt') as g_in, open(txt_path, 'w') as f_out:
                shutil.copyfileobj(g_in, f_out)
        return txt_path
    return gz_path  # 이미 .txt

def edgelist_to_csr(txt: pathlib.Path):
    print(f"[parse] {txt.name}")
    src_list, dst_list = [], []
    with open(txt) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            s, d = map(int, line.split())
            src_list.append(s)
            dst_list.append(d)
    src = np.asarray(src_list, dtype=np.int64)
    dst = np.asarray(dst_list, dtype=np.int64)
    n   = int(max(src.max(), dst.max()) + 1)
    print(f"  nodes: {n:,}  edges: {len(src):,}")
    order = np.lexsort((dst, src))
    src, dst = src[order], dst[order]

    indptr = np.zeros(n + 1, dtype=np.int64)
    np.add.at(indptr, src + 1, 1)
    np.cumsum(indptr, out=indptr)
    return indptr, dst

def to_dgap(indptr: np.ndarray, dst: np.ndarray):
    print("[dgap] computing…")
    dst = dst.astype(np.uint32, copy=False)
    out = np.empty_like(dst, dtype=np.uint32)
    for u in range(len(indptr)-1):
        beg, end = indptr[u], indptr[u+1]
        if beg == end: continue
        first = dst[beg]
        out[beg] = first  # 첫 값은 절대 ID
        np.subtract(dst[beg+1:end], dst[beg:end-1], out=out[beg+1:end])
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True,
        choices=list(URLS.keys()) + ["uk2002"],
        help="predefined dataset name")
    ap.add_argument("--raw",
        help="이미 추출된 edge list (.txt) 경로")
    args = ap.parse_args()

    if args.raw:
        txt_path = pathlib.Path(args.raw)
        if not txt_path.exists():
            raise SystemExit(f"{txt_path} not found")
    else:
        txt_path = ensure_txt(args.name)

    indptr, dst = edgelist_to_csr(txt_path)
    dgap = to_dgap(indptr, dst)

    out_npy = DATA_DIR / f"{args.name}_dgap.npy"
    np.save(out_npy, dgap.astype(np.uint32))
    print(f"[saved] {out_npy}  ({dgap.size:,} ints)")

if __name__ == "__main__":
    main()
