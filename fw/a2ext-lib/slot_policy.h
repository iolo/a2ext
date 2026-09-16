#pragma once
#include "a2ext.h"

typedef struct { bool c800_owned; } a2ext_slot_policy_t;

static inline bool a2ext_slot_selected(a2ext_slot_policy_t *state, const a2ext_cycle_t *c) {
    if (c->address == 0xcfff) { state->c800_owned = false; return false; }
    if (c->address >= 0xc100 && c->address < 0xc800) {
        state->c800_owned = c->iosel;
    }
    if (c->devsel && c->address >= 0xc090 && c->address <= 0xc0ff) return true;
    if (c->iosel && c->address >= 0xc100 && c->address < 0xc800) return true;
    return c->iostrb && state->c800_owned && c->address >= 0xc800 && c->address < 0xcfff;
}
