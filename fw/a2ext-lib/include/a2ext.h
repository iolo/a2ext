#pragma once
#include <stdbool.h>
#include <stdint.h>

/* Initialize the prepared module with all Apple II lines released. */
void a2ext_init(void);

typedef struct {
    uint16_t address;
    uint8_t data;
    bool read;
    bool devsel, iosel, iostrb; /* true when asserted */
} a2ext_cycle_t;

typedef struct {
    uint32_t blocks;
    uint32_t overflows;
    uint32_t epoch; /* changes whenever the capture stream loses continuity */
} a2ext_capture_stats_t;

static inline a2ext_cycle_t a2ext_decode_cycle(uint32_t word) {
    a2ext_cycle_t cycle = {
        .address = (uint16_t)word, .data = (uint8_t)(word >> 16),
        .read = (word & (1u << 24)) != 0,
        .devsel = (word & (1u << 25)) == 0,
        .iosel = (word & (1u << 26)) == 0,
        .iostrb = (word & (1u << 27)) == 0,
    };
    return cycle;
}

/* Start, poll, and stop on one core. DMA IRQ1 is owned on that core. */
bool a2ext_capture_start(void);
void a2ext_capture_stop(void);
bool a2ext_next_cycle(a2ext_cycle_t *cycle);
a2ext_capture_stats_t a2ext_capture_stats(void);
