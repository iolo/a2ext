#include "hardware/clocks.h"
#include "hardware/irq.h"
#include "pico/stdlib.h"
#include "a2ext_pins.h"
#include "runtime.h"
#include "applebus/buffers.h"
#include "render/render.h"
#include "fonts/textfont.h"
#include <string.h>
struct dvi_inst dvi0;
uint8_t color_mode;
bool mono_rendering, color_support, reload_colors;
static struct dvi_serialiser_cfg serial = {
    .pio=pio1, .sm_tmds={0,1,2},
    .pins_tmds={A2EXT_GPIO_DVI_D0_P,A2EXT_GPIO_DVI_D1_P,A2EXT_GPIO_DVI_D2_P},
    .pins_clk=A2EXT_GPIO_DVI_CLK_P, .invert_diffpairs=false,
};
int main(void) {
    /* Experimental: 252 MHz exceeds the rated 150 MHz. No voltage override. */
    set_sys_clock_khz(252000,true);
    video_capture_start();
#ifdef APPLE_MODEL_IIPLUS
    memcpy(character_rom,textfont_iiplus_us,CHARACTER_ROM_SIZE);
#else
    memcpy(character_rom,textfont_iie_us_enhanced,CHARACTER_ROM_SIZE);
#endif
    DVI_INIT_RESOLUTION(640);
    tmds_color_load();
    dvi0.timing=&dvi_timing_640x480p_60hz; dvi0.ser_cfg=&serial;
    uint lock=spin_lock_claim_unused(true);
    dvi_init(&dvi0,lock,lock);
    dvi_register_irqs_this_core(&dvi0,DMA_IRQ_0);
    dvi_start(&dvi0);
    for (;;) {
        soft_switches=atomic_load(&video_shadow.flags);
        video_snapshot(apple_memory,aux_memory);
        render_frame(); video_poll();
    }
}
