#include "a2ext.h"
#include "pico/stdlib.h"
#include "hardware/clocks.h"

int main(void) {
    a2ext_init();
    set_sys_clock_khz(126000, true);
    if (!a2ext_capture_start()) panic("capture resource initialization failed");
    a2ext_cycle_t cycle;
    /* Passive capture bring-up; active slot service follows in step 14. */
    while (true) {
        if (!a2ext_next_cycle(&cycle)) tight_loop_contents();
    }
}
