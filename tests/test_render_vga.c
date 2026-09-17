#include "pico.h"
#include "buffers.h"
#include "render.h"
#include "vga.h"
#include "textfont/textfont.h"
#include "render_fixture.h"
#include "render_output.h"
uint64_t host_time;
static struct vga_scanline scanlines[8];
static unsigned head;
void vga_prepare_frame(void) { memset(pixels,0,sizeof pixels); row=0; }
void vga_skip_lines(unsigned n) { row+=n; assert(row<=480); }
struct vga_scanline *vga_prepare_scanline(void) {
    struct vga_scanline *s=&scanlines[head++%8]; memset(s,0,sizeof *s); return s;
}
void vga_submit_scanline(struct vga_scanline *s) {
    assert(s->length<328);
    for(unsigned repeat=0;repeat<=s->repeat_count;++repeat) {
        unsigned x=0; assert(row<480);
        for(unsigned i=0;i<s->length*2;++i) {
            uint16_t v=(s->data[i/2]>>(16*(i&1)))&0xffff;
            const unsigned lengths[9]={1,0,0,0,8,7,4,3,2};
            unsigned jump=v>>9; assert(jump<9 && lengths[jump]);
            for(unsigned n=0;n<lengths[jump];++n) {
                assert(x<640);
                pixels[row][x][0]=((v>>6)&7)*255/7;
                pixels[row][x][1]=((v>>3)&7)*255/7;
                pixels[row][x][2]=(v&7)*255/7; ++x;
            }
        }
        assert(x>=560 && x<=640); ++row;
    }
}
int main(int argc,char **argv) {
    assert(argc==2);
#ifdef APPLE_MODEL_IIPLUS
    fixture(false); memcpy(character_rom,textfont_iiplus_us,sizeof character_rom);
#else
    fixture(true); memcpy(character_rom,textfont_iie_us_enhanced,sizeof character_rom);
#endif
    a2ext_shadow_copy(&shadow,0,main_memory,sizeof main_memory);
    a2ext_shadow_copy(&shadow,1,aux_memory,sizeof aux_memory);
    render_init();
    for(unsigned i=0;i<sizeof cases/sizeof *cases;++i) {
        uint32_t f=cases[i].flags;
#ifdef APPLE_MODEL_IIPLUS
        f &= 15;
#endif
        soft_switches=f&15; soft_80col=f&A2EXT_80COL; soft_80store=f&A2EXT_80STORE;
        soft_altcharset=f&A2EXT_ALTCHAR; soft_dhires=f&A2EXT_DHIRES;
        render_frame(); assert(row==432); save_frame(argv[1],cases[i].name);
    }
    host_time=1000000; soft_switches=A2EXT_TEXT; soft_80col=soft_80store=soft_altcharset=false;
    render_frame(); assert(row==432); save_frame(argv[1],"text40_flash");
    puts("VGA: actual renderer replay, scanline bounds and dimensions passed");
}
