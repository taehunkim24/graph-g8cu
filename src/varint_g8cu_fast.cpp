#include <cstdint>
#include <cstring>

static inline uint8_t len_code(uint32_t v){ return v<=0xFF?0:v<=0xFFFF?1:v<=0xFFFFFF?2:3; }

/*──────── encode – 헤더 없는 1-B Fast-Path + nibble ───────*/
extern "C" size_t G8CU_FAST_encodeArray32(const uint32_t* in,size_t n,uint8_t* out){
    const uint32_t* p=in; uint8_t* o=out;
    while(p+4<=in+n){
        if(p[0]<=0xFF&&p[1]<=0xFF&&p[2]<=0xFF&&p[3]<=0xFF){   // ① Fast-Path
            *o++=uint8_t(p[0]);*o++=uint8_t(p[1]);
            *o++=uint8_t(p[2]);*o++=uint8_t(p[3]);
            p+=4; continue;
        }
        uint8_t* hdr=o++; uint8_t bits=0;                     // ② nibble(2 값)
        for(int i=0;i<2&&p<in+n;i++){
            uint32_t v=*p++; uint8_t lc=len_code(v);
            bits|=lc<<(4*i);
            for(int b=0;b<=lc;b++){*o++=uint8_t(v); v>>=8;}
        }
        *hdr=bits;
    }
    /* 남은 1-3 값 */
    while(p<in+n){
        uint8_t* hdr=o++; uint8_t bits=0;
        for(int i=0;i<2&&p<in+n;i++){
            uint32_t v=*p++; uint8_t lc=len_code(v);
            bits|=lc<<(4*i);
            for(int b=0;b<=lc;b++){*o++=uint8_t(v); v>>=8;}
        }
        *hdr=bits;
    }
    return size_t(o-out);
}

/*──────── decode ──────────────────────────────────────────*/
extern "C" size_t G8CU_FAST_decodeArray32(const uint8_t* in,uint32_t* out,size_t n){
    const uint8_t* p=in; uint32_t* o=out; const uint32_t* end=out+n;
    while(o+4<=end){                       // 먼저 4 값 루프
        /* ① Fast-Path 후보: 남은 값 ≥4 && 다음 4 바이트 모두 <256 ? */
        if(p[0]<0x40){ break; }            // nibble 헤더(0x00-0x3F)이면 탈출
        *o++=*p++; *o++=*p++; *o++=*p++; *o++=*p++;  // 4 byte 복사
    }
    while(o<end){                          // nibble 경로
        uint8_t hdr=*p++;
        for(int i=0;i<2&&o<end;i++){
            uint8_t lc=(hdr>>(4*i))&3;
            uint32_t v=0;
            for(int b=0;b<=lc;b++) v|=uint32_t(*p++)<<(8*b);
            *o++=v;
        }
    }
    return size_t(p-in);
}
