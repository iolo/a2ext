#include "runtime.h"
#include "pico/multicore.h"
#include "pico/stdlib.h"
#include <stdio.h>
a2ext_shadow_t video_shadow;
static _Atomic bool ready;
static _Atomic uint32_t overflows, cycles;
static char diagnostic_line[160];
static unsigned diagnostic_position;
static uint32_t output_errors;
static void __not_in_flash_func(bus_core)(void) {
    if (!a2ext_capture_start()) panic("capture resources unavailable");
    atomic_store(&ready, true);
    a2ext_cycle_t c;
    while (true) {
        bool available = a2ext_next_cycle(&c);
        a2ext_capture_stats_t stats = a2ext_capture_stats();
        a2ext_shadow_epoch(&video_shadow, stats.epoch);
        atomic_store_explicit(&overflows, stats.overflows, memory_order_relaxed);
        if (available) {
            a2ext_shadow_apply(&video_shadow, &c);
            /* Single writer: avoid an expensive atomic RMW each bus cycle. */
            uint32_t n = atomic_load_explicit(&cycles, memory_order_relaxed);
            atomic_store_explicit(&cycles, n+1, memory_order_relaxed);
        }
    }
}
static void diagnostic(uint32_t byte) {
    if (byte != '?' || diagnostic_line[diagnostic_position]) return;
    diagnostic_position=0;
    snprintf(diagnostic_line,sizeof diagnostic_line,"\r\ncycles=%lu overflow=%lu known=%08lx resets=%lu drops=%lu video_errors=%lu\r\n",
        (unsigned long)atomic_load(&cycles), (unsigned long)atomic_load(&overflows),
        (unsigned long)atomic_load(&video_shadow.known), (unsigned long)atomic_load(&video_shadow.resets),
        (unsigned long)a2ext_callback_drops(), (unsigned long)output_errors);

}
void video_capture_start(void) {
#ifdef APPLE_MODEL_IIPLUS
    a2ext_shadow_init(&video_shadow, false);
#else
    a2ext_shadow_init(&video_shadow, true);
#endif
    a2ext_init();
    a2ext_on_receive(diagnostic);
    multicore_launch_core1(bus_core);
    while (!atomic_load(&ready)) tight_loop_contents();
}
void video_snapshot(uint8_t *main_ram, uint8_t *aux_ram) {
    a2ext_shadow_copy(&video_shadow,false,main_ram,0x6000);
    a2ext_shadow_copy(&video_shadow,true,aux_ram,0x6000);
}
void video_output_errors(uint32_t errors) { output_errors=errors; }
void video_poll(void) {
    a2ext_poll();
    for (unsigned i=0; i<16 && diagnostic_line[diagnostic_position]; ++i) {
        if (!a2ext_try_send((uint8_t)diagnostic_line[diagnostic_position])) break;
        ++diagnostic_position;
    }
}
