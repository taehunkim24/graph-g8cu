#include "varint_g8cu.h"
#include <cstddef>
#include <cstdint>

extern "C" {
size_t G8CU_encodeArray32(const uint32_t* in, size_t n,
                          uint8_t* out) {      // byte output
    return g8cu::encode32(in, n, out);
}
size_t G8CU_decodeArray32(const uint8_t* in,
                          uint32_t* out, size_t n) { // n values
    return g8cu::decode32(in, out, n);
}
}
