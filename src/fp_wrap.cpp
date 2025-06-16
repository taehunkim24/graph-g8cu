#include "VarIntG8IU.h"          // ← FastPFor/headers/VarIntG8IU.h
#include <cstddef>
#include <cstdint>

using FastPForLib::VarIntG8IU;

extern "C" {

size_t VarIntG8IU_encodeArray32(const uint32_t* in, size_t n,
                                uint32_t* out) {
    VarIntG8IU coder;
    size_t outWords = 0;
    coder.encodeArray(in, n, out, outWords);
    return outWords;
}

size_t VarIntG8IU_decodeArray32(const uint32_t* in,
                                uint32_t* out, size_t n) {
    VarIntG8IU coder;
    size_t dummy = 0;
    const uint32_t* p = coder.decodeArray(in, n, out, dummy);
    return static_cast<size_t>(p - in);      // 소비한 word 수
}

} // extern "C"
