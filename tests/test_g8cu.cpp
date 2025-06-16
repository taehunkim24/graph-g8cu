#include "varint_g8cu.h"
#include <cstdio>
#include <cstdint>
#include <vector>
#include <cassert>

int main() {
    std::vector<uint32_t> in = {
        1,2,3,4,5,6,7,8,                  // group 0
        9,10,11,12,13,14,15,16,           // group 1
        17,18                             // group 2 (partial)
    };
    size_t n = in.size();

    std::vector<uint8_t>  enc(n * 5);
    size_t used = g8cu::encode32(in.data(), n, enc.data());

    std::vector<uint32_t> out(n);
    size_t consumed = g8cu::decode32(enc.data(), out.data(), n);

    printf("used=%zu  consumed=%zu\n", used, consumed);
    for (size_t i=0;i<n;i++)
        printf("%2zu  in=%u  out=%u%s\n",
               i, in[i], out[i], (in[i]==out[i]?"":"  <-- mismatch"));
    assert(in == out && "round-trip failed");
}
