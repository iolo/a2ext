#pragma once
#include "a2ext.h"
#include <stddef.h>
#include <stdatomic.h>

enum {
    A2EXT_TEXT=1u, A2EXT_MIXED=2u, A2EXT_HIRES=4u, A2EXT_PAGE2=8u,
    A2EXT_80STORE=1u<<8, A2EXT_AUXREAD=1u<<9, A2EXT_AUXWRITE=1u<<10,
    A2EXT_ALTZP=1u<<11, A2EXT_80COL=1u<<13, A2EXT_ALTCHAR=1u<<14,
    A2EXT_DHIRES=1u<<15,
};
#define A2EXT_SHADOW_FLAGS (0xef0fu)
#define A2EXT_BANK_BYTES 65536u
/* Single capture-core writer, atomic byte readers. No frame coherence promise. */
typedef struct {
    _Atomic uint8_t ram[2][A2EXT_BANK_BYTES];
    _Atomic uint8_t valid[2][A2EXT_BANK_BYTES/8];
    _Atomic uint32_t flags, known, losses, resets;
    uint32_t epoch;
    bool iie, reset_held;
} a2ext_shadow_t;
void a2ext_shadow_init(a2ext_shadow_t *s, bool iie);
void a2ext_shadow_reset(a2ext_shadow_t *s);
void a2ext_shadow_epoch(a2ext_shadow_t *s, uint32_t epoch);
void a2ext_shadow_apply(a2ext_shadow_t *s, const a2ext_cycle_t *c);
bool a2ext_shadow_byte(const a2ext_shadow_t *s, bool aux, uint16_t address, uint8_t *value);
void a2ext_shadow_copy(const a2ext_shadow_t *s, bool aux, uint8_t *dest, size_t length);
