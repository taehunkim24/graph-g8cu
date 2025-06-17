#include "varint_g8cu.h"
#include <smmintrin.h>   // SSE4.1
#include <cstring>

namespace g8cu {

constexpr int GROUP = 4;                 // 4 values per descriptor

/*──────────────────── helper: length code (0‒3) ───────────────────*/
static inline uint8_t len_code(uint32_t v) {
    return v <= 0xFF ? 0 : v <= 0xFFFF ? 1 : v <= 0xFFFFFF ? 2 : 3;
}

/*───────────────────────── encode32 ─────────────────────────*/
size_t encode32(const uint32_t *in, size_t n, uint8_t *out) {
    const uint32_t *p = in;
    uint8_t       *o = out;

    while (p < in + n) {
        /* FAST‑PATH ─ Δ‑gap 값 네 개 모두 1 byte */
        if (p + GROUP <= in + n &&
            p[0] <= 0xFF && p[1] <= 0xFF && p[2] <= 0xFF && p[3] <= 0xFF) {
            *o++ = 0xFF;                 // 특수 표식(descriptor=0xFF)
            *o++ = uint8_t(p[0]);
            *o++ = uint8_t(p[1]);
            *o++ = uint8_t(p[2]);
            *o++ = uint8_t(p[3]);
            p += GROUP;
            continue;
        }

        /* 일반 G8CU (2‑bit len × 4) */
        uint8_t *desc = o++;
        uint8_t  bits = 0;
        for (int i = 0; i < GROUP; ++i) {
            uint32_t v  = (p < in + n) ? *p++ : 0;
            uint8_t  lc = len_code(v);          // 0–3
            bits |= lc << (i * 2);              // bit‑pack
            for (int b = 0; b <= lc; ++b) {
                *o++ = uint8_t(v);
                v >>= 8;
            }
        }
        *desc = bits;
    }
    return size_t(o - out);
}

/*───────────────────────── decode32 ─────────────────────────*/
size_t decode32(const uint8_t *in, uint32_t *out, size_t n) {
    const uint8_t *p   = in;
    uint32_t      *o   = out;
    const uint32_t *end = out + n;

    /* ── NB: SSE4.1 fast‑path는 descriptor 0xFF(4×1‑byte) 스트림을
            최대한 벡터화. 다른 패턴은 동일 스칼라 코드 재사용 ── */
    while (o < end) {
#if defined(__SSE4_1__)
        /* 연속된 0xFF 패턴을 128‑bit 단위로 처리 */
        while (o + 4 <= end && *p == 0xFF) {
            /* 4 data bytes를 uint32_t로 확장 → 4×uint32 store */
            uint32_t fourBytes;
            std::memcpy(&fourBytes, p + 1, 4);        // 안전한 load (unaligned OK)
            __m128i v8  = _mm_cvtsi32_si128(int(fourBytes)); // [b3|b2|b1|b0]
            __m128i v32 = _mm_cvtepu8_epi32(v8);            // zero‑extend to 4×uint32
            _mm_storeu_si128(reinterpret_cast<__m128i*>(o), v32);
            p += 5;   // 1(desc)+4(bytes)
            o += 4;
        }
        if (o >= end) break;  // 종료 체크
#endif
        /* 스칼라 경로 (descriptor != 0xFF) */
        uint8_t desc = *p++;
        if (desc == 0xFF) {
            /* SSE가 꺼져있거나 4개 이하 잔량이 남은 경우 */
            for (int i = 0; i < GROUP && o < end; ++i)
                *o++ = *p++;
            continue;
        }
        for (int i = 0; i < GROUP && o < end; ++i) {
            uint8_t code = (desc >> (i * 2)) & 3;
            uint32_t v = 0;
            for (int b = 0; b <= code; ++b)
                v |= uint32_t(*p++) << (8 * b);
            *o++ = v;
        }
    }
    return size_t(p - in);
}

} // namespace g8cu

/*──────── C-symbol wrappers — required by benchmark script ─────*/
extern "C" {

    size_t G8CU_encodeArray32(const uint32_t* in, size_t n, uint8_t* out)
    {
        return g8cu::encode32(in, n, out);
    }
    
    size_t G8CU_decodeArray32(const uint8_t* in, uint32_t* out, size_t n)
    {
        return g8cu::decode32(in, out, n);
    }
    
    } // extern "C"