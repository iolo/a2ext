#include "a2ext.h"
#include "pico/stdlib.h"
#include "hardware/clocks.h"
#include "pico/multicore.h"
#include <stdio.h>

#ifdef A2EXT_DEMO_ACTIVE
#include "firmware_rom.h"
#endif

static volatile uint32_t captured, lost;

#ifdef A2EXT_DEMO_ACTIVE
static bool __not_in_flash_func(slot_access)(const a2ext_cycle_t *c, uint8_t *reply) {
    if (c->devsel) {
        if (c->read) {
            if ((c->address & 15) == 0) {
                *reply = multicore_fifo_rvalid() ? (uint8_t)multicore_fifo_pop_blocking() : 0;
                return true;
            }
            if ((c->address & 15) == 1) {
                *reply = (multicore_fifo_rvalid() ? 0x40 : 0) | (multicore_fifo_wready() ? 0x80 : 0);
                return true;
            }
        } else {
            if ((c->address & 15) == 0 && multicore_fifo_wready()) multicore_fifo_push_blocking(c->data);
            if ((c->address & 15) == 1) { a2ext_irq(false); a2ext_nmi(false); }
        }
    } else if (c->read) {
        *reply = firmware_rom[c->address & 0x0fff];
        return true;
    }
    return false;
}
#endif

static void bus_core(void) {
#ifdef A2EXT_DEMO_ACTIVE
    if (!a2ext_slot_enable(slot_access)) panic("slot responder unavailable");
    while (true) {
        a2ext_slot_poll();
        if (a2ext_slot_faulted()) lost = 1;
    }
#else
    if (!a2ext_capture_start()) panic("capture unavailable");
    a2ext_cycle_t cycle;
    while (true) {
        if (a2ext_next_cycle(&cycle)) ++captured;
        lost = a2ext_capture_stats().overflows;
    }
#endif
}

static void message(const char *s) { while (*s) a2ext_send((uint8_t)*s++); }
static void reset_event(bool asserted) { message(asserted ? "\r\nRESET asserted\r\n" : "\r\nRESET released\r\n"); }
static void receive(uint32_t value) {
#ifdef A2EXT_DEMO_ACTIVE
    if (value == 0x1b) a2ext_irq(true);
    else if (value == 0x0e) a2ext_nmi(true);
    else if (multicore_fifo_wready()) multicore_fifo_push_blocking(value);
#else
    if (value == '?') {
        char status[96];
        snprintf(status, sizeof status, "\r\ncycles=%lu lost=%lu callback_drops=%lu\r\n",
                 (unsigned long)captured, (unsigned long)lost, (unsigned long)a2ext_callback_drops());
        message(status);
    }
#endif
}

int main(void) {
#ifdef A2EXT_DEMO_ACTIVE
    set_sys_clock_khz(252000, true);
#else
    set_sys_clock_khz(126000, true);
#endif
    a2ext_init();
    multicore_launch_core1(bus_core);
    a2ext_on_receive(receive);
    a2ext_on_reset(reset_event);
    message("a2ext demo\r\n");
    while (true) {
        a2ext_poll();
#ifdef A2EXT_DEMO_ACTIVE
        if (multicore_fifo_rvalid()) a2ext_send((uint8_t)multicore_fifo_pop_blocking());
#endif
        tight_loop_contents();
    }
}
