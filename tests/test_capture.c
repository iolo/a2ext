#include <assert.h>
#include <stdio.h>
#include "a2ext.h"
#include "capture_queue.h"

int main(void) {
    /* Exercise every address bit and both data extremes, independent of GPIO IDs. */
    for (unsigned address = 0; address < 65536; ++address) {
        a2ext_cycle_t c = a2ext_decode_cycle(0x0e000000u | (0x5au << 16) | address);
        assert(c.address == address && c.data == 0x5a && !c.read);
        assert(!c.devsel && !c.iosel && !c.iostrb);
    }
    a2ext_cycle_t c = a2ext_decode_cycle(0x01ffffffu);
    assert(c.address == 0xffff && c.data == 0xff && c.read);
    assert(c.devsel && c.iosel && c.iostrb);

    a2ext_capture_queue_t q = {0};
    assert(!q.ready[q.read_block]);
    assert(!a2ext_capture_complete(&q, 1)); /* out-of-order completion */
    for (unsigned block = 0; block < 8; ++block) {
        assert(a2ext_capture_complete(&q, block & 1u));
        for (unsigned word = 0; word < A2EXT_CAPTURE_BLOCK_WORDS; ++word) {
            assert(q.ready[q.read_block]);
            assert(q.read_position == word && q.read_block == (block & 1u));
            a2ext_capture_advance(&q);
        }
        assert(!q.ready[q.read_block ^ 1u]);
    }
    q = (a2ext_capture_queue_t){0};
    assert(a2ext_capture_complete(&q, 0));
    a2ext_capture_advance(&q); /* partially consumed block must not be overwritten */
    assert(!a2ext_capture_complete(&q, 1));
    puts("capture: address decoding, ordered delivery, wrap, and overwrite detection passed");
}
