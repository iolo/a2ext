/* Adapted from AppleII-VGA (Mark Aikens / David Kuder), MIT; see LICENSE. */
#include "render.h"
#include "buffers.h"
void render_init(void) { generate_hires_tables(); }
void render_frame(void) {
    update_text_flasher();
#ifdef A2EXT_VIDEO_TEST_PATTERN
    render_vga_testpattern();
#else
    switch (soft_switches & SOFTSW_MODE_MASK) {
    case 0: render_lores(); break;
    case SOFTSW_MIX_MODE: render_mixed_lores(); break;
    case SOFTSW_HIRES_MODE: render_hires(false); break;
    case SOFTSW_HIRES_MODE|SOFTSW_MIX_MODE: render_hires(true); break;
    default: render_text(); break;
    }
#endif
}
