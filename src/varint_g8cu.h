#pragma once
#include <cstddef>
#include <cstdint>

namespace g8cu {
/// encode Δ-gap 배열 → 압축 버퍼
/// @return out 버퍼에 쓰인 byte 수
size_t encode32(const uint32_t* in, size_t n, uint8_t* out);

/// decode 압축 버퍼 → Δ-gap 배열
/// @return in 버퍼에서 소비한 byte 수
size_t decode32(const uint8_t* in, uint32_t* out, size_t n);
}  // namespace g8cu
