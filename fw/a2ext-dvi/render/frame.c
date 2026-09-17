#include "applebus/buffers.h"
#include "render.h"
void render_frame(void) {
#ifdef A2EXT_VIDEO_TEST_PATTERN
    for (unsigned y=0;y<192;++y) {
        dvi_get_scanline(buf);
        for (unsigned x=0;x<320;++x) {
            unsigned color=(x/20)%16;
            buf[x]=tmds_lorescolor[3*color+2];
            buf[x+320]=tmds_lorescolor[3*color+1];
            buf[x+640]=tmds_lorescolor[3*color];
        }
        dvi_send_scanline(buf);
    }
#else
    update_text_flasher();
    bool dbl=(soft_switches&(SOFTSW_DGR|SOFTSW_80COL))==(SOFTSW_DGR|SOFTSW_80COL);
    switch (soft_switches&SOFTSW_MODE_MASK) {
    case 0: if(dbl) render_dgr(); else render_lores(); break;
    case SOFTSW_MIX_MODE: if(dbl) render_mixed_dgr(); else render_mixed_lores(); break;
    case SOFTSW_HIRES_MODE: if(dbl) render_dhgr(); else render_hires(); break;
    case SOFTSW_HIRES_MODE|SOFTSW_MIX_MODE: if(dbl) render_mixed_dhgr(); else render_mixed_hires(); break;
    default: render_text(); break;
    }
#endif
}
