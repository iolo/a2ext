#include "hardware/clocks.h"
#include "pico/stdlib.h"
#include "runtime.h"
#include "buffers.h"
#include "render.h"
#include "vga.h"
#include "textfont/textfont.h"
#include <string.h>
static void snapshot(void) {
    uint32_t f=atomic_load(&video_shadow.flags);
    soft_switches=f&15;
    soft_80col=f&A2EXT_80COL; soft_80store=f&A2EXT_80STORE;
    soft_altcharset=f&A2EXT_ALTCHAR; soft_dhires=f&A2EXT_DHIRES;
    soft_video7_mode=VIDEO7_MODE_140x192;
    video_snapshot(main_memory,aux_memory);
}
int main(void) {
    set_sys_clock_khz(126000,true);
    video_capture_start();
#ifdef APPLE_MODEL_IIPLUS
    memcpy(character_rom,textfont_iiplus_us,sizeof character_rom);
#else
    memcpy(character_rom,textfont_iie_us_enhanced,sizeof character_rom);
#endif
    render_init(); vga_init();
    for (;;) { snapshot(); render_frame(); video_poll(); }
}
