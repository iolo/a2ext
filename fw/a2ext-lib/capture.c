#include "a2ext.h"
#include "a2ext_pins.h"
#include "a2ext.pio.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/irq.h"
#include "hardware/sync.h"
#include "capture_queue.h"
#include "a2ext_internal.h"

#define CAPTURE_SM 0u
#define BLOCK_WORDS A2EXT_CAPTURE_BLOCK_WORDS
#define CAPTURE_HZ 126000000u
#define RXSTALL (1u << (PIO_FDEBUG_RXSTALL_LSB + CAPTURE_SM))

static uint32_t blocks[2][BLOCK_WORDS];
static int channels[2] = {-1, -1};
static uint32_t channel_mask;
static unsigned program_offset;
static volatile bool fault;
static volatile a2ext_capture_queue_t queue;
static volatile a2ext_capture_stats_t stats;
static bool running;

/* DMA writes the other block while the CPU consumes a completed block. */
static void __not_in_flash_func(capture_irq)(void) {
    uint32_t pending = dma_hw->ints1 & channel_mask;
    dma_hw->ints1 = pending;
    if (!pending) return;
    unsigned done = queue.completion;
    if (pending != (1u << channels[done]) || (pio0->fdebug & RXSTALL) ||
        !a2ext_capture_complete(&queue, done)) {
        fault = true;
        pio_sm_set_enabled(pio0, CAPTURE_SM, false);
        return;
    }
    __dmb();
    ++stats.blocks;
    dma_channel_set_write_addr(channels[done], blocks[done], false);
    dma_channel_set_trans_count(channels[done], BLOCK_WORDS, false);
}

static void capture_reset_stream(void) {
    pio_sm_set_enabled(pio0, CAPTURE_SM, false);
    for (unsigned i = 0; i < 2; ++i) {
        dma_channel_set_irq1_enabled(channels[i], false);
        dma_channel_abort(channels[i]);
    }
    dma_hw->ints1 = channel_mask;
    pio_sm_clear_fifos(pio0, CAPTURE_SM);
    pio_sm_restart(pio0, CAPTURE_SM);
    pio_sm_exec(pio0, CAPTURE_SM, pio_encode_jmp(program_offset));
    pio0->fdebug = RXSTALL;
    queue = (a2ext_capture_queue_t){0};
    fault = false;
    for (unsigned i = 0; i < 2; ++i) {
        dma_channel_set_write_addr(channels[i], blocks[i], false);
        dma_channel_set_trans_count(channels[i], BLOCK_WORDS, false);
        dma_channel_set_irq1_enabled(channels[i], true);
    }
    dma_start_channel_mask(1u << channels[0]);
    pio_sm_set_enabled(pio0, CAPTURE_SM, true);
}

bool a2ext_capture_start(void) {
    if (running) return true;
    if (clock_get_hz(clk_sys) < CAPTURE_HZ) return false;
    if (pio_sm_is_claimed(pio0, CAPTURE_SM) ||
        !pio_can_add_program(pio0, &a2ext_capture_program)) return false;
    channels[0] = dma_claim_unused_channel(false);
    channels[1] = dma_claim_unused_channel(false);
    if (channels[0] < 0 || channels[1] < 0) {
        for (unsigned i = 0; i < 2; ++i)
            if (channels[i] >= 0) dma_channel_unclaim(channels[i]);
        return false;
    }
    pio_sm_claim(pio0, CAPTURE_SM);
    pio_set_gpio_base(pio0, 0);
    program_offset = pio_add_program(pio0, &a2ext_capture_program);
    pio_sm_config cfg = a2ext_capture_program_get_default_config(program_offset);
    sm_config_set_in_pins(&cfg, A2EXT_GPIO_ADDR_BASE);
    sm_config_set_in_shift(&cfg, false, true, 28);
    sm_config_set_fifo_join(&cfg, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&cfg, (float)clock_get_hz(clk_sys) / CAPTURE_HZ);
    pio_sm_init(pio0, CAPTURE_SM, program_offset, &cfg);
    channel_mask = (1u << channels[0]) | (1u << channels[1]);
    for (unsigned i = 0; i < 2; ++i) {
        dma_channel_config dc = dma_channel_get_default_config(channels[i]);
        channel_config_set_transfer_data_size(&dc, DMA_SIZE_32);
        channel_config_set_read_increment(&dc, false);
        channel_config_set_write_increment(&dc, true);
        channel_config_set_dreq(&dc, pio_get_dreq(pio0, CAPTURE_SM, false));
        channel_config_set_chain_to(&dc, channels[i ^ 1u]);
        channel_config_set_high_priority(&dc, true);
        dma_channel_configure(channels[i], &dc, blocks[i], &pio0->rxf[CAPTURE_SM], BLOCK_WORDS, false);
    }
    irq_set_exclusive_handler(DMA_IRQ_1, capture_irq);
    irq_set_priority(DMA_IRQ_1, PICO_HIGHEST_IRQ_PRIORITY);
    irq_set_enabled(DMA_IRQ_1, true);
    ++stats.epoch;
    running = true;
    capture_reset_stream();
    return true;
}

void a2ext_capture_stop(void) {
    if (!running) return;
    irq_set_enabled(DMA_IRQ_1, false);
    pio_sm_set_enabled(pio0, CAPTURE_SM, false);
    for (unsigned i = 0; i < 2; ++i) {
        dma_channel_set_irq1_enabled(channels[i], false);
        dma_channel_abort(channels[i]);
        dma_channel_unclaim(channels[i]);
    }
    dma_hw->ints1 = channel_mask;
    pio_remove_program(pio0, &a2ext_capture_program, program_offset);
    pio_sm_unclaim(pio0, CAPTURE_SM);
    irq_remove_handler(DMA_IRQ_1, capture_irq);
    running = false;
    ++stats.epoch;
}

bool __not_in_flash_func(a2ext_next_cycle)(a2ext_cycle_t *cycle) {
    if (!running || !cycle) return false;
    uint32_t saved = save_and_disable_interrupts();
    if (fault || (pio0->fdebug & RXSTALL)) {
        ++stats.overflows;
        ++stats.epoch;
        capture_reset_stream();
        restore_interrupts(saved);
        return false;
    }
    if (!queue.ready[queue.read_block]) {
        restore_interrupts(saved);
        return false;
    }
    __dmb();
    uint32_t word = blocks[queue.read_block][queue.read_position];
    a2ext_capture_advance(&queue);
    restore_interrupts(saved);
    *cycle = a2ext_decode_cycle(word);
    a2ext_latch_cycle(cycle);
    return true;
}

a2ext_capture_stats_t a2ext_capture_stats(void) {
    uint32_t saved = save_and_disable_interrupts();
    a2ext_capture_stats_t snapshot = stats;
    restore_interrupts(saved);
    return snapshot;
}
