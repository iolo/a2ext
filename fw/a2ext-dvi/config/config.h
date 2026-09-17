#pragma once
#include "pico/stdlib.h"
#include "dvi.h"
enum { MACHINE_II, MACHINE_PRAVETZ, MACHINE_IIE, MACHINE_IIE_ENH };
#ifdef APPLE_MODEL_IIPLUS
#define current_machine MACHINE_II
#else
#define current_machine MACHINE_IIE_ENH
#endif
#define language_switch false
extern uint8_t color_mode;
#define cfg_color_style 0
extern bool reload_colors;
