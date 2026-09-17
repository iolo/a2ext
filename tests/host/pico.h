#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
typedef unsigned int uint;
#define __in_flash(x)
#define __not_in_flash_func(x) x
#define __time_critical_func(x) x
extern uint64_t host_time;
static inline uint64_t time_us_64(void) { return host_time; }
