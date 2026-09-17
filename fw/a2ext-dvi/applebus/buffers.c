/* Renderer frame copies; physical capture is provided by a2ext-lib. */
#include "buffers.h"
uint8_t apple_memory[MAX_ADDRESS], aux_memory[MAX_ADDRESS];
uint8_t character_rom[2*CHARACTER_ROM_SIZE];
volatile uint32_t soft_switches, internal_flags;
volatile uint8_t *text_p1=apple_memory+0x400, *text_p2=apple_memory+0x800;
volatile uint8_t *text_p3=aux_memory+0x400, *text_p4=aux_memory+0x800;
volatile uint8_t *hgr_p1=apple_memory+0x2000, *hgr_p2=apple_memory+0x4000;
volatile uint8_t *hgr_p3=aux_memory+0x2000, *hgr_p4=aux_memory+0x4000;
