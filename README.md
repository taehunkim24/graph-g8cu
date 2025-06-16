# Δ-Gap Integer-Compression Benchmark  
_Comparing **streamvbyte (SSE only)** vs **g8cu (SSE only)** on four SNAP graphs_  
> **Datasets**: `dblp`, `google`, `livejournal`, `youtube`  
> **Goal**: measure **compression ratio (bpe)** and **encode/decode speed** under the _same_ SIMD level (SSE).

---

## 1  Requirements
| Item | Version / Note |
|------|----------------|
| **Ubuntu** | 20.04 LTS / 22.04 LTS (WSL2 OK) |
| **g++** | ≥ 9  (`-mssse3 -msse4.1` flags) |
| **Python** | ≥ 3.9  (venv recommended) |
| Tools | `wget git cmake` |

```bash
sudo apt update && sudo apt install -y build-essential python3-venv \
    wget git cmake
```

## 2 Directory Layout
```bash
graph_G8CU/   
├─ src/   
│  ├─ varint_g8cu.cpp  
│  ├─ varint_g8cu.h   
│  └─ …   
├─ scripts/   
│  ├─ prep_graph.py         # Δ-gap → NPY   
│  └─ benchmark_baseline.py # benchmark runner   
├─ build/         # compiled .so files   
└─ data/          # *_dgap.npy (auto-generated)   
```

## 3 Python env & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install numpy pandas pyfastpfor==0.4.1   # streamvbyte (SSE) inside
```

## 4 Prepare Graph Data
Generate Δ-gap arrays (takes a few minutes each).
```bash
python scripts/prep_graph.py --name dblp
python scripts/prep_graph.py --name google
python scripts/prep_graph.py --name livejournal
python scripts/prep_graph.py --name youtube
```

## 5 Build g8cu (SSE)
```bash
mkdir -p build
g++ -O3 -std=c++17 -fPIC -msse4.1 -I src \
    src/varint_g8cu.cpp \
    -shared -o build/libg8cu.so

export LD_LIBRARY_PATH=$PWD/build:$LD_LIBRARY_PATH
```

Verify symbols:
```bash
nm -D build/libg8cu.so | grep G8CU_
# shows G8CU_encodeArray32 / G8CU_decodeArray32
```

## 6 Run Benchmarks
### 6-1 streamvbyte (SSE baseline)
```bash
python scripts/benchmark_baseline.py            # default = streamvbyte
# results/streamvbyte.csv produced
```
### 6-2 g8cu (SSE)
```bash
python scripts/benchmark_baseline.py --codec g8cu
# results/g8cu.csv produced
```

## 7 Example Results
| Graph       | streamvbyte<br>enc / dec MB/s | g8cu<br>enc / dec MB/s | bpe *(both)* |
| ----------- | ----------------------------- | ---------------------- | ------------ |
| dblp        | 1.6 / 1.7 GB/s                | **3.4 / 2.0 GB/s**     | 10.00        |
| google      | 4.1 / 3.3 GB/s                | **3.3 / 1.9 GB/s**     | 10.00        |
| livejournal | 2.7 / 3.2 GB/s                | **2.8 / 2.9 GB/s**     | 10.02        |
| youtube     | 4.4 / 8.6 GB/s                | **2.3 / 2.9 GB/s**     | 10.01        |
g8cu encoder is up to 2× faster on some graphs; decoder is slower or similar.

Compression ratio identical (≈10 bits per edge).


## 8 Conclusion
With SSE-level SIMD only, g8cu offers higher encode throughput on 2 of 4 graphs but no space savings versus streamvbyte.
Further AVX2 experiments were dropped—time cost outweighed benefit for this project.