#include "applebus/buffers.h"
#include "render/render.h"
#include "fonts/textfont.h"
#include "render_fixture.h"
#include "render_output.h"
uint64_t host_time;
struct dvi_inst dvi0;
bool mono_rendering,color_support,reload_colors;
uint8_t color_mode;
static uint32_t scanlines[8][962];
static bool busy[8];
void queue_remove_blocking_u32(queue_t *q,void *out) {
    (void)q;
    for (unsigned i=0;i<8;++i) if (!busy[i]) {
        busy[i]=true; memset(scanlines[i],0,sizeof scanlines[i]);
        scanlines[i][0]=scanlines[i][961]=0xdeadbeef;
        *(uint32_t**)out=&scanlines[i][1]; return;
    }
    assert(!"exhausted scanline pool");
}
static uint8_t decode(uint16_t t) {
    uint8_t q=(t&0xff)^((t&0x200)?0xff:0);
    return (q^(q<<1)^((t&0x100)?0:0xfe))&0xff;
}
void queue_add_blocking_u32(queue_t *q,const void *in) {
    (void)q; const uint32_t *buf=*(uint32_t*const*)in;
    unsigned index=0;
    while(index<8 && buf!=&scanlines[index][1]) ++index;
    assert(index<8 && busy[index]);
    assert(scanlines[index][0]==0xdeadbeef && scanlines[index][961]==0xdeadbeef);
    busy[index]=false;
    for(unsigned y=0;y<2;++y) {
        assert(row<432);
        for(unsigned x=0;x<640;++x)
            for(unsigned rgb=0;rgb<3;++rgb) {
                uint32_t v=buf[(2-rgb)*320+x/2]; assert(v<0x100000);
                pixels[row][x][rgb]=decode(v>>(10*(x&1)));
            }
        ++row;
    }
}
int main(int argc,char **argv) {
    assert(argc==2);
#ifdef APPLE_MODEL_IIPLUS
    fixture(false); memcpy(character_rom,textfont_iiplus_us,2048);
#else
    fixture(true); memcpy(character_rom,textfont_iie_us_enhanced,2048);
#endif
    a2ext_shadow_copy(&shadow,0,apple_memory,sizeof apple_memory);
    a2ext_shadow_copy(&shadow,1,aux_memory,sizeof aux_memory);
    DVI_INIT_RESOLUTION(640); tmds_color_load();
    for(unsigned i=0;i<sizeof cases/sizeof *cases;++i) {
        soft_switches=cases[i].flags;
#ifdef APPLE_MODEL_IIPLUS
        soft_switches &= 15;
#endif
        row=48; memset(pixels,0,sizeof pixels);
        render_frame(); assert(row==432); save_frame(argv[1],cases[i].name);
    }
    host_time=1000000; soft_switches=A2EXT_TEXT; row=48; memset(pixels,0,sizeof pixels);
    render_frame(); assert(row==432); save_frame(argv[1],"text40_flash");
    puts("DVI: actual renderer replay, TMDS decoding and dimensions passed");
}
