#pragma once
#include "pico.h"
#define DELAYED_COPY_CODE(n) n
#define DELAYED_COPY_DATA(n) n
typedef int queue_t;
struct dvi_inst { queue_t q_tmds_free, q_tmds_valid; };
void queue_remove_blocking_u32(queue_t *q, void *out);
void queue_add_blocking_u32(queue_t *q, const void *in);
