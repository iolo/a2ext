#pragma once
#include <string.h>
/* Startup palette copies do not claim another DMA channel. Size is bytes. */
#define memcpy32(dest, src, size) memcpy(dest, src, size)
