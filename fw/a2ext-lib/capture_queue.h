#pragma once
#include <stdbool.h>
#include <stdint.h>

#define A2EXT_CAPTURE_BLOCK_WORDS 1024u

/* One core plus its DMA IRQ own this state. Caller serializes CPU access. */
typedef struct {
    bool ready[2];
    unsigned read_block, read_position, completion;
} a2ext_capture_queue_t;

static inline bool a2ext_capture_complete(volatile a2ext_capture_queue_t *q, unsigned done) {
    if (done != q->completion || q->ready[done ^ 1u]) return false;
    q->ready[done] = true;
    q->completion ^= 1u;
    return true;
}

/* Call only after copying the current word out of the completed DMA block. */
static inline void a2ext_capture_advance(volatile a2ext_capture_queue_t *q) {
    if (++q->read_position == A2EXT_CAPTURE_BLOCK_WORDS) {
        q->ready[q->read_block] = false;
        q->read_block ^= 1u;
        q->read_position = 0;
    }
}
