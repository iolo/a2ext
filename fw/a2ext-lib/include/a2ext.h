#pragma once
#include <stdbool.h>
#include <stdint.h>

/* Initialize the prepared module with all Apple II lines released. */
void a2ext_init(void);

typedef struct {
    uint16_t address;
    uint8_t data;
    bool read;
    bool reset; /* sampled /RES asserted; ordered with passive capture */
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
        .reset = (word & (1u << 29)) == 0,
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

/* Getters refer to the last cycle returned by a2ext_next_cycle on its core. */
bool a2ext_has_cycle(void);
uint16_t a2ext_getaddr(void);
uint8_t a2ext_getdata(void);
void a2ext_putdata(uint8_t data);
bool a2ext_try_putdata(uint8_t data);
void a2ext_irq(bool on);
void a2ext_nmi(bool on);

/* Register and poll callbacks on the core which called init (normally core 0).
 * Handlers run from poll, not IRQ context. NULL unregisters. SYNC counter=0
 * disables counting; otherwise one callback per counter falling edges.
 */
void a2ext_on_reset(void (*handler)(bool on));
void a2ext_on_sync(void (*handler)(void), uint32_t counter);
void a2ext_on_receive(void (*handler)(uint32_t data));
void a2ext_send(uint8_t data); /* blocking UART0 byte, 115200 8N1 */
void a2ext_poll(void);
uint32_t a2ext_callback_drops(void);

/* Experimental responder, explicit opt-in and same-core ownership. Handler
 * must be bounded/nonblocking. Return true with *reply set for a read reply;
 * write callbacks receive the delayed, valid write-data sample.
 */
typedef bool (*a2ext_slot_handler_t)(const a2ext_cycle_t *cycle, uint8_t *reply);
bool a2ext_slot_enable(a2ext_slot_handler_t handler);
void a2ext_slot_disable(void);
void a2ext_slot_poll(void);
bool a2ext_slot_faulted(void);
