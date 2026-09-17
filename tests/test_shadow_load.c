/* Concurrent desktop stress of the real atomic shadow and frame-copy routines.
   This does not emulate RP2350 DMA or establish target throughput. */
#include "a2ext_shadow.h"
#include <assert.h>
#include <stdio.h>
#include <threads.h>
static a2ext_shadow_t shadow;
static _Atomic bool ready, done;
static unsigned copies;
static int reader(void *arg) {
    (void)arg;
    struct { uint32_t before; uint8_t ram[0x6000]; uint32_t after; } copy={.before=0x12345678,.after=0x76543210};
    atomic_store(&ready,true);
    do {
        a2ext_shadow_copy(&shadow,false,copy.ram,sizeof copy.ram);
        assert(copy.before==0x12345678 && copy.after==0x76543210);
        ++copies;
    } while (!atomic_load(&done));
    return 0;
}
int main(void) {
    a2ext_shadow_init(&shadow,false);
    thrd_t thread; assert(thrd_create(&thread,reader,NULL)==thrd_success);
    while (!atomic_load(&ready)) thrd_yield();
    for(unsigned pass=0;pass<32;++pass) {
        if(pass==16) a2ext_shadow_epoch(&shadow,1);
        for(unsigned a=0;a<0xc000;++a) {
            uint32_t raw=0x2e000000u|((uint32_t)(uint8_t)(a^pass)<<16)|a;
            a2ext_cycle_t c=a2ext_decode_cycle(raw); a2ext_shadow_apply(&shadow,&c);
        }
        a2ext_cycle_t reset={.reset=true};
        a2ext_shadow_apply(&shadow,&reset); a2ext_shadow_apply(&shadow,&reset);
        reset.reset=false; a2ext_shadow_apply(&shadow,&reset);
    }
    atomic_store(&done,true); thrd_join(thread,NULL);
    assert(copies>0 && atomic_load(&shadow.resets)==32);
    for(unsigned a=1;a<0xc000;++a) {
        uint8_t value; assert(a2ext_shadow_byte(&shadow,false,a,&value));
        assert(value==(uint8_t)(a^31));
    }
    printf("shadow concurrent load: 1,572,864 decoded writes, %u snapshots, reset/loss recovery passed (desktop only)\n",copies);
}
