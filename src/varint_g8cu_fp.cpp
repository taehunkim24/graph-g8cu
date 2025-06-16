#include <cstdint>
#include <cstring>

// 0=1B, 1=2B, 2=3B, 3=4B
static inline uint8_t len_code(uint32_t v){
    return v <= 0xFF ? 0 : v <= 0xFFFF ? 1 : v <= 0xFFFFFF ? 2 : 3;
}

/*──────────────────────── encode ───────────────────────*/
extern "C"
size_t G8CU_FP_encodeArray32(const uint32_t* in, size_t n, uint8_t* out){
    const uint32_t* p = in;
    uint8_t*        o = out;

    while(p + 4 <= in + n){
        /* ① 헤더 없는 Fast-Path (4 × 1 B) */
        if(p[0]<=0xFF && p[1]<=0xFF && p[2]<=0xFF && p[3]<=0xFF){
            *o++ = 0xF0;                    // sentinel
            *o++ = uint8_t(p[0]); *o++ = uint8_t(p[1]);
            *o++ = uint8_t(p[2]); *o++ = uint8_t(p[3]);
            p += 4;
            continue;
        }

        /* ② nibble 헤더 – 두 값 처리 */
        uint8_t* hdr = o++;  uint8_t bits = 0;
        for(int i=0;i<2 && p<in+n; ++i){
            uint32_t v = *p++;  uint8_t lc = len_code(v);
            bits |= lc << (4*i);
            for(int b=0;b<=lc; ++b){ *o++ = uint8_t(v); v >>= 8; }
        }
        *hdr = bits;
    }

    /* 남은 1–3 값 */
    while(p < in + n){
        uint8_t* hdr = o++;  uint8_t bits = 0;
        for(int i=0;i<2 && p<in+n; ++i){
            uint32_t v = *p++;  uint8_t lc = len_code(v);
            bits |= lc << (4*i);
            for(int b=0;b<=lc; ++b){ *o++ = uint8_t(v); v >>= 8; }
        }
        *hdr = bits;
    }
    return size_t(o - out);                 // bytes written
}

/*──────────────────────── decode ───────────────────────*/
extern "C"
size_t G8CU_FP_decodeArray32(const uint8_t* in, uint32_t* out, size_t n){
    const uint8_t* p = in;
    uint32_t*      o = out;
    const uint32_t* end = out + n;

    while(o < end){
        uint8_t hdr = *p++;

        /* ① Fast-Path sentinel */
        if(hdr == 0xF0){
            for(int i=0;i<4 && o<end; ++i) *o++ = *p++;
            continue;
        }

        /* ② nibble 헤더 */
        for(int i=0;i<2 && o<end; ++i){
            uint8_t lc = (hdr >> (4*i)) & 3;
            uint32_t v = 0;
            for(int b=0; b<=lc; ++b)
                v |= uint32_t(*p++) << (8*b);
            *o++ = v;
        }
    }
    return size_t(p - in);                  // bytes read
}
