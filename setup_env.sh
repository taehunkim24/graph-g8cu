#!/usr/bin/env bash
set -e

sudo apt-get update
sudo apt-get install -y build-essential gcc-12 g++-12 numactl \
                        python3.10-venv linux-tools-common

# WSL2인지 확인
if grep -qEi "(Microsoft|WSL)" /proc/version; then
  # WSL2: generic 패키지로 perf 설치
  sudo apt-get install -y linux-tools-generic
else
  # 일반 우분투: 커널 버전에 맞춰 설치
  KREL=$(uname -r)
  sudo apt-get install -y "linux-tools-$KREL"
fi

# 나머지 동일
git clone https://github.com/lemire/FastPFor.git
cmake -S FastPFor -B FastPFor/build -DCMAKE_BUILD_TYPE=Release
cmake --build FastPFor/build -j"$(nproc)"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip pandas matplotlib tqdm
