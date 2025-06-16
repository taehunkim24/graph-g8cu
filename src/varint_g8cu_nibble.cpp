#include "varint_g8cu.h"
#include <immintrin.h>
#include <cstring>


// -------- 상수 변경 --------
constexpr int GROUP = 4;          // 값 4개가 한 그룹
// ---------------------------

namespace g8cu {

// ───── 디코드 LUT ───────────────────────────────────────────
struct Tbl { uint8_t len; __m256i mask; };
alignas(32) static Tbl LUT[256];

static __m256i make_mask(uint8_t desc) {
    uint8_t shuf[32];
    std::memset(shuf, 0x80, sizeof(shuf));   // ← *NEW*  0x80 = shuffle-zero
    uint8_t ofs = 0;
    for (int i = 0; i < 8; ++i) {
        uint8_t code = (desc >> (i * 2)) & 3;
        uint8_t len  = code + 1;             // 1~4 bytes
        for (uint8_t b = 0; b < len; ++b)
            shuf[i * 4 + b] = ofs + b;       // 유효 바이트만 복사
        ofs += len;
    }
    return _mm256_loadu_si256(reinterpret_cast<const __m256i*>(shuf));
}


static bool init = [] {
    for (int d = 0; d < 256; ++d) {
        LUT[d].len  = 0;
        for (int i = 0; i < 8; ++i)
            LUT[d].len += ((d >> (i * 2)) & 3) + 1;
        LUT[d].mask = make_mask(static_cast<uint8_t>(d));
    }
    return true;
}();

// ───── 디코더 ───────────────────────────────────────────────
// 파일 상단 인클루드·LUT 정의는 그대로 두고
// ──────────────────────────────────────────────
// 기존 decode32 함수 전체를 아래 스칼라 버전으로 교체
/*──────── decode ─────────────────────────*/
extern "C" size_t G8CU_NIB_decodeArray32(const uint8_t* in,
    uint32_t* out, size_t n)
{
const uint8_t* p = in;
uint32_t*      o = out;
const uint32_t* end = out + n;

while (o < end) {
uint8_t hdr = *p++;
if (hdr == 0xF0) {                       // Fast-Path
for (int i=0;i<4 && o<end;i++) *o++ = *p++;
continue;
}
for (int i=0;i<2 && o<end;i++){
uint8_t lc=(hdr>>(4*i))&0xF;
uint32_t v=0;
for(int b=0;b<=lc;b++) v|=uint32_t(*p++)<<(8*b);
*o++ = v;
}
}
return size_t(p - in);
}



// ───── 인코더(스칼라) ────────────────────────────────────────
static inline uint8_t len_code(uint32_t v) {
    return v <= 0xFF ? 0 : v <= 0xFFFF ? 1 : v <= 0xFFFFFF ? 2 : 3;
}

/*──────── encode (Fast-Path+Nibble) ───────*/
extern "C" size_t G8CU_NIB_encodeArray32(const uint32_t* in, size_t n,
    uint8_t* out)
{
const uint32_t* p = in;
uint8_t*        o = out;
while (p + 4 <= in + n) {                          // 4-값 단위 Fast-Path 판정
if (p[0]<=0xFF && p[1]<=0xFF && p[2]<=0xFF && p[3]<=0xFF) {
*o++ = 0xF0;                              // sentinel
*o++ = uint8_t(p[0]); *o++ = uint8_t(p[1]);
*o++ = uint8_t(p[2]); *o++ = uint8_t(p[3]);
p += 4;
continue;
}

/* 두 값씩 nibble 인코딩 */
uint8_t* hdr_pos = o++;   uint8_t hdr = 0;
for (int i=0;i<2 && p<in+n;i++) {
uint32_t v = *p++;  uint8_t lc = len_code(v);
hdr |= lc << (4*i);
for (int b=0;b<=lc;b++){ *o++=uint8_t(v); v>>=8; }
}
*hdr_pos = hdr;
}

/* 남은 1–3 값 처리 */
while (p < in + n) {
uint8_t* hdr_pos = o++;   uint8_t hdr = 0;
for (int i=0;i<2 && p<in+n;i++){
uint32_t v=*p++; uint8_t lc=len_code(v);
hdr|=lc<<(4*i);
for(int b=0;b<=lc;b++){*o++=uint8_t(v); v>>=8;}
}
*hdr_pos=hdr;
}
return size_t(o - out);      // bytes written
}



} // namespace g8cu
