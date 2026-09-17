#pragma once
#include "a2ext_shadow.h"
#include <assert.h>
static a2ext_shadow_t shadow;
static void access_bus(uint16_t a, uint8_t d, bool read) {
    a2ext_cycle_t c={.address=a,.data=d,.read=read}; a2ext_shadow_apply(&shadow,&c);
}
static void fixture(bool iie) {
    a2ext_shadow_init(&shadow,iie);
    for(unsigned a=0xc000;a<=0xc00e;a+=2) access_bus(a,0,false);
    access_bus(0xc07e,0,false); access_bus(0xc05f,0,true);
    for(unsigned bank=0;bank<(iie?2u:1u);++bank) {
        access_bus(0xc004+bank,0,false);
        for(unsigned a=0x400;a<0xc00;++a)
            access_bus(a,(uint8_t)(a*13+(a>>7)+bank*7),false);
        for(unsigned a=0x2000;a<0x6000;++a)
            access_bus(a,(uint8_t)((a*17)^(a>>4)^(bank*0x55)),false);
    }
}
static const struct {const char *name; uint32_t flags;} cases[]={
    {"text40",A2EXT_TEXT}, {"text80",A2EXT_TEXT|A2EXT_80COL},
    {"lores",0}, {"double_lores",A2EXT_80COL|A2EXT_DHIRES},
    {"hires",A2EXT_HIRES}, {"double_hires",A2EXT_HIRES|A2EXT_80COL|A2EXT_DHIRES},
    {"mixed_lores",A2EXT_MIXED}, {"mixed_hires",A2EXT_HIRES|A2EXT_MIXED},
    {"mixed_double_lores",A2EXT_MIXED|A2EXT_80COL|A2EXT_DHIRES},
    {"mixed_double_hires",A2EXT_HIRES|A2EXT_MIXED|A2EXT_80COL|A2EXT_DHIRES},
    {"page2",A2EXT_TEXT|A2EXT_PAGE2}, {"store_page1",A2EXT_TEXT|A2EXT_PAGE2|A2EXT_80STORE},
    {"altcharset",A2EXT_TEXT|A2EXT_80COL|A2EXT_ALTCHAR},
};
