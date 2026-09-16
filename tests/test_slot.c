#include <assert.h>
#include <stdio.h>
#include "slot_policy.h"

int main(void) {
    a2ext_slot_policy_t s = {0};
    a2ext_cycle_t c = {.address=0xc800, .read=true, .iostrb=true};
    assert(!a2ext_slot_selected(&s,&c));
    c=(a2ext_cycle_t){.address=0xc700,.read=true,.iosel=true};
    assert(a2ext_slot_selected(&s,&c) && s.c800_owned);
    c=(a2ext_cycle_t){.address=0xc800,.read=true,.iostrb=true};
    assert(a2ext_slot_selected(&s,&c));
    c.address=0xcfff;
    assert(!a2ext_slot_selected(&s,&c) && !s.c800_owned);
    c.address=0xc800;
    assert(!a2ext_slot_selected(&s,&c));
    c=(a2ext_cycle_t){.address=0xc300,.read=true,.iosel=true};
    assert(a2ext_slot_selected(&s,&c));
    c=(a2ext_cycle_t){.address=0xc600,.read=true};
    assert(!a2ext_slot_selected(&s,&c) && !s.c800_owned);
    c=(a2ext_cycle_t){.address=0xc0f0,.read=false,.devsel=true};
    assert(a2ext_slot_selected(&s,&c));
    c.address=0x2000; /* Even a bogus select must not authorize ordinary RAM. */
    assert(!a2ext_slot_selected(&s,&c));
    puts("slot policy: selection, C800 ownership, CFFF release, and unrelated accesses passed");
}
