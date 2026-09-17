#include "a2ext_shadow.h"
#include <string.h>
#ifdef PICO_ON_DEVICE
#include "pico.h"
#define SHADOW_HOT(name) __not_in_flash_func(name)
#else
#define SHADOW_HOT(name) name
#endif
#define RELAXED memory_order_relaxed

void a2ext_shadow_init(a2ext_shadow_t *s, bool iie) {
    memset(s, 0, sizeof *s);
    s->iie = iie;
    atomic_store(&s->flags, A2EXT_TEXT);
    /* II/II+ have no MMU banking. Initial display state is still unknown. */
    atomic_store(&s->known, iie ? 0 : (A2EXT_SHADOW_FLAGS & ~15u));
}

void a2ext_shadow_reset(a2ext_shadow_t *s) {
    atomic_fetch_add_explicit(&s->resets, 1, RELAXED);
    /* Conservatively reacquire switches from observed accesses. Never invent
       a cleared framebuffer or treat a warm reset as a power-on RAM reset. */
    atomic_store_explicit(&s->known, s->iie ? 0 : (A2EXT_SHADOW_FLAGS & ~15u), RELAXED);
}

void a2ext_shadow_epoch(a2ext_shadow_t *s, uint32_t epoch) {
    if (s->epoch == epoch) return;
    s->epoch = epoch;
    for (unsigned bank=0; bank<2; ++bank)
        for (unsigned i=0; i<A2EXT_BANK_BYTES/8; ++i)
            atomic_store_explicit(&s->valid[bank][i], 0, RELAXED);
    atomic_store_explicit(&s->known, s->iie ? 0 : (A2EXT_SHADOW_FLAGS & ~15u), RELAXED);
    atomic_fetch_add_explicit(&s->losses, 1, RELAXED);
}

void SHADOW_HOT(a2ext_shadow_apply)(a2ext_shadow_t *s, const a2ext_cycle_t *c) {
    if (c->reset && !s->reset_held) a2ext_shadow_reset(s);
    s->reset_held = c->reset;
    if (c->reset) return;
    uint16_t a = c->address;
    uint32_t flags = atomic_load_explicit(&s->flags, RELAXED);
    uint32_t known = atomic_load_explicit(&s->known, RELAXED);
    if (a >= 0xc000) {
        uint32_t bit = 0;
        bool on = a & 1;
        if (a >= 0xc050 && a <= 0xc057) {
            static const uint32_t bits[] = {A2EXT_TEXT,A2EXT_MIXED,A2EXT_PAGE2,A2EXT_HIRES};
            bit = bits[(a-0xc050)/2];
        } else if (s->iie && !c->read && a <= 0xc00f) {
            static const uint32_t bits[] = {A2EXT_80STORE,A2EXT_AUXREAD,A2EXT_AUXWRITE,0,A2EXT_ALTZP,0,A2EXT_80COL,A2EXT_ALTCHAR};
            bit = bits[(a-0xc000)/2];
        } else if (s->iie && (a == 0xc05e || a == 0xc05f)) {
            bit = A2EXT_DHIRES; on = !(a & 1);
        }
        if (bit) {
            atomic_store_explicit(&s->flags, (flags & ~bit) | (on ? bit : 0), RELAXED);
            atomic_store_explicit(&s->known, known | bit, RELAXED);
        }
        return; /* I/O, ROM and language-card banks are not ordinary RAM. */
    }
    if (c->read) return;
    bool aux = false;
    if (s->iie) {
        uint32_t needed;
        if (a < 0x200) {
            needed = A2EXT_ALTZP;
            aux = flags & A2EXT_ALTZP;
        } else {
            needed = A2EXT_AUXWRITE;
            aux = flags & A2EXT_AUXWRITE;
            bool text = a >= 0x400 && a < 0x800;
            bool hires = a >= 0x2000 && a < 0x4000;
            if (text || hires) {
                needed |= A2EXT_80STORE;
                if (flags & A2EXT_80STORE) {
                    if (hires) needed |= A2EXT_HIRES;
                    if (text || (flags & A2EXT_HIRES)) {
                        needed &= ~A2EXT_AUXWRITE;
                        needed |= A2EXT_PAGE2;
                        aux = flags & A2EXT_PAGE2;
                    }
                }
            }
        }
        if ((known & needed) != needed) return;
    }
    atomic_store_explicit(&s->ram[aux][a], c->data, RELAXED);
    /* One writer. Release pairs with validity reads before loading the byte. */
    uint8_t mask = atomic_load_explicit(&s->valid[aux][a>>3], RELAXED);
    atomic_store_explicit(&s->valid[aux][a>>3], mask | (1u << (a&7)), memory_order_release);
}

bool a2ext_shadow_byte(const a2ext_shadow_t *s, bool aux, uint16_t a, uint8_t *v) {
    bool valid = atomic_load_explicit(&s->valid[aux][a>>3], memory_order_acquire) & (1u << (a&7));
    *v = valid ? atomic_load_explicit(&s->ram[aux][a], RELAXED) : 0;
    return valid;
}

void a2ext_shadow_copy(const a2ext_shadow_t *s, bool aux, uint8_t *dest, size_t n) {
    if (n > A2EXT_BANK_BYTES) n = A2EXT_BANK_BYTES;
    for (size_t i=0; i<n; ++i) (void)a2ext_shadow_byte(s, aux, (uint16_t)i, &dest[i]);
}
