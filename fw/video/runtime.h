#pragma once
#include "a2ext_shadow.h"
extern a2ext_shadow_t video_shadow;
void video_capture_start(void);
void video_snapshot(uint8_t *main_ram, uint8_t *aux_ram);
void video_poll(void);
