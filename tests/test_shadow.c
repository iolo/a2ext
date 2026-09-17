#include "a2ext_shadow.h"
#include <assert.h>
#include <stdio.h>
static a2ext_shadow_t s;
static void access(uint16_t a, uint8_t d, bool read) {
    a2ext_cycle_t c={.address=a,.data=d,.read=read}; a2ext_shadow_apply(&s,&c);
}
static void expect(bool aux, uint16_t a, uint8_t want) {
    uint8_t got; assert(a2ext_shadow_byte(&s,aux,a,&got)); assert(got==want);
}
int main(void) {
    uint8_t v;
    a2ext_shadow_init(&s,true);
    access(0x400,0xaa,false); assert(!a2ext_shadow_byte(&s,0,0x400,&v));
    access(0xc000,0,true); assert(!(atomic_load(&s.known)&A2EXT_80STORE));
    access(0xc000,0,false); access(0xc004,0,false); access(0xc008,0,false);
    access(0x400,0x11,false); expect(0,0x400,0x11);
    access(0xc005,0,false); access(0x400,0x22,false); expect(1,0x400,0x22);
    access(0xc001,0,false); access(0xc054,0,true);
    access(0x400,0x33,false); expect(0,0x400,0x33); /* 80STORE overrides AUXWRITE */
    access(0xc055,0,true); access(0x400,0x44,false); expect(1,0x400,0x44);
    access(0xc004,0,false); access(0xc056,0,true);
    access(0x2000,0x55,false); expect(0,0x2000,0x55);
    access(0xc057,0,true); access(0x2000,0x66,false); expect(1,0x2000,0x66);
    access(0xc009,0,false); access(0x100,0x77,false); expect(1,0x100,0x77);
    access(0xc00d,0,false); access(0xc00f,0,false); access(0xc05e,0,true);
    assert((atomic_load(&s.flags)&(A2EXT_80COL|A2EXT_ALTCHAR|A2EXT_DHIRES))==(A2EXT_80COL|A2EXT_ALTCHAR|A2EXT_DHIRES));
    access(0xc050,0,true); access(0xc053,0,true);
    assert((atomic_load(&s.flags)&7)==(A2EXT_HIRES|A2EXT_MIXED));
    a2ext_shadow_reset(&s); expect(1,0x2000,0x66); assert(!atomic_load(&s.known));
    a2ext_shadow_epoch(&s,1); assert(!a2ext_shadow_byte(&s,1,0x2000,&v));
    a2ext_shadow_init(&s,false);
    access(0xc005,0,false); access(0xc00d,0,false);
    access(0x400,0xa5,false); expect(0,0x400,0xa5);
    assert(!(atomic_load(&s.flags)&(A2EXT_AUXWRITE|A2EXT_80COL)));
    access(0x400,0x5a,true); expect(0,0x400,0xa5);
    access(0xc100,0x88,false); assert(!a2ext_shadow_byte(&s,0,0xc100,&v));
    a2ext_shadow_reset(&s); expect(0,0x400,0xa5);
    puts("shadow: II/IIe bank precedence, switches, unknown bytes, reset retention, epochs passed");
}
