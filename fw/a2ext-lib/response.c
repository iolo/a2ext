#include "a2ext.h"
#include "a2ext_pins.h"
#include "a2ext_internal.h"
#include "slot_policy.h"
#include "a2ext.pio.h"
#include "response.pio.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/sync.h"

#define RESPONSE_SM 0u
#define LATE_SM 1u
#define RESPONSE_HZ 126000000u
#define TAG_MASK 0x00ffffffu

static bool active, failed, pending, decided, reply_context;
static uint32_t tag;
static unsigned early_offset, late_offset;
static a2ext_cycle_t early_cycle;
static a2ext_slot_policy_t policy;
static a2ext_slot_handler_t slot_handler;

bool a2ext_slot_enable(a2ext_slot_handler_t handler) {
    if (active || !handler || clock_get_hz(clk_sys) < RESPONSE_HZ ||
        pio_sm_is_claimed(pio2, RESPONSE_SM) || pio_sm_is_claimed(pio0, LATE_SM) ||
        !pio_can_add_program(pio2, &a2ext_response_program) ||
        !pio_can_add_program(pio0, &a2ext_capture_program)) return false;
    pio_sm_claim(pio2, RESPONSE_SM);
    pio_sm_claim(pio0, LATE_SM);
    pio_set_gpio_base(pio2, 0);
    pio_set_gpio_base(pio0, 0);
    early_offset = pio_add_program(pio2, &a2ext_response_program);
    late_offset = pio_add_program(pio0, &a2ext_capture_program);
    pio_sm_config ec = a2ext_response_program_get_default_config(early_offset);
    sm_config_set_in_pins(&ec, A2EXT_GPIO_ADDR_BASE);
    sm_config_set_in_shift(&ec, false, false, 32);
    sm_config_set_out_pins(&ec, A2EXT_GPIO_DATA_BASE, 8);
    sm_config_set_out_shift(&ec, true, false, 32);
    sm_config_set_jmp_pin(&ec, A2EXT_GPIO_PHI0);
    sm_config_set_clkdiv(&ec, (float)clock_get_hz(clk_sys)/RESPONSE_HZ);
    pio_sm_init(pio2, RESPONSE_SM, early_offset+a2ext_response_offset_cycle_start, &ec);
    pio_sm_put(pio2, RESPONSE_SM, TAG_MASK);
    pio_sm_exec(pio2, RESPONSE_SM, pio_encode_pull(false, true));
    pio_sm_exec(pio2, RESPONSE_SM, pio_encode_mov(pio_y, pio_osr));
    pio_sm_set_consecutive_pindirs(pio2, RESPONSE_SM, A2EXT_GPIO_DATA_BASE, 8, false);
    for (unsigned pin = A2EXT_GPIO_D0; pin <= A2EXT_GPIO_D7; ++pin) pio_gpio_init(pio2, pin);
    pio_sm_config lc = a2ext_capture_program_get_default_config(late_offset);
    sm_config_set_in_pins(&lc, A2EXT_GPIO_ADDR_BASE);
    sm_config_set_in_shift(&lc, false, true, 28);
    sm_config_set_fifo_join(&lc, PIO_FIFO_JOIN_RX);
    sm_config_set_clkdiv(&lc, (float)clock_get_hz(clk_sys)/RESPONSE_HZ);
    pio_sm_init(pio0, LATE_SM, late_offset, &lc);
    pio0->fdebug = 1u << (PIO_FDEBUG_RXSTALL_LSB + LATE_SM);
    pio2->fdebug = 1u << (PIO_FDEBUG_RXSTALL_LSB + RESPONSE_SM);
    pending = decided = reply_context = failed = false;
    policy = (a2ext_slot_policy_t){0};
    slot_handler = handler;
    active = true;
    /* PIO2's next block is PIO0: start both on exactly the same cycle. */
    pio_enable_sm_multi_mask_in_sync(pio2, 0, 1u << RESPONSE_SM, 1u << LATE_SM);
    return true;
}

void a2ext_slot_disable(void) {
    if (!active) return;
    /* Release the physical data pads before stopping the timed PIO program. */
    for (unsigned pin = A2EXT_GPIO_D0; pin <= A2EXT_GPIO_D7; ++pin) {
        gpio_set_dir(pin, GPIO_IN);
        gpio_set_function(pin, GPIO_FUNC_SIO);
    }
    pio_sm_set_enabled(pio2, RESPONSE_SM, false);
    pio_sm_set_enabled(pio0, LATE_SM, false);
    pio_remove_program(pio2, &a2ext_response_program, early_offset);
    pio_remove_program(pio0, &a2ext_capture_program, late_offset);
    pio_sm_unclaim(pio2, RESPONSE_SM);
    pio_sm_unclaim(pio0, LATE_SM);
    policy.c800_owned = false;
    active = pending = reply_context = false;
}

bool a2ext_slot_faulted(void) { return failed; }

bool __not_in_flash_func(a2ext_try_putdata)(uint8_t data) {
    uint32_t saved = save_and_disable_interrupts();
    bool eligible = active && reply_context && tag && gpio_get(A2EXT_GPIO_PHI0) &&
        gpio_get(A2EXT_GPIO_RES_N) && !pio_sm_is_tx_fifo_full(pio2, RESPONSE_SM) &&
        !(pio2->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + RESPONSE_SM)));
    if (eligible) pio_sm_put(pio2, RESPONSE_SM, ((uint32_t)data << 24) | tag);
    restore_interrupts(saved);
    return eligible;
}

static void __not_in_flash_func(try_read)(void) {
    if (decided || !early_cycle.read || !gpio_get(A2EXT_GPIO_PHI0)) return;
    /* Slot selects can arrive after the early address sample. */
    uint32_t pins = gpio_get_all();
    a2ext_cycle_t c = early_cycle;
    c.devsel = !(pins & (1u << A2EXT_GPIO_DEVSEL_N));
    c.iosel = !(pins & (1u << A2EXT_GPIO_IOSEL_N));
    c.iostrb = !(pins & (1u << A2EXT_GPIO_IOSTRB_N));
    if (!(c.devsel || c.iosel || c.iostrb) && c.address != 0xcfff) return;
    decided = true;
    if (!a2ext_slot_selected(&policy, &c)) return;
    a2ext_latch_cycle(&c);
    uint8_t reply = 0;
    reply_context = true;
    if (slot_handler(&c, &reply)) (void)a2ext_try_putdata(reply);
    reply_context = false;
}

void __not_in_flash_func(a2ext_slot_poll)(void) {
    if (!active) return;
    if (!gpio_get(A2EXT_GPIO_RES_N)) {
        policy.c800_owned = false;
        /* Continue draining without responding until reset releases. */
    }
    if ((pio2->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + RESPONSE_SM))) ||
        (pio0->fdebug & (1u << (PIO_FDEBUG_RXSTALL_LSB + LATE_SM)))) {
        failed = true;
        a2ext_slot_disable();
        return;
    }
    if (!pending) {
        if (pio_sm_get_rx_fifo_level(pio2, RESPONSE_SM) < 2) return;
        tag = pio_sm_get(pio2, RESPONSE_SM);
        early_cycle = a2ext_decode_cycle(pio_sm_get(pio2, RESPONSE_SM));
        pending = true;
        decided = false;
    }
    if (gpio_get(A2EXT_GPIO_RES_N)) try_read();
    if (pio_sm_is_rx_fifo_empty(pio0, LATE_SM)) return;
    a2ext_cycle_t late = a2ext_decode_cycle(pio_sm_get(pio0, LATE_SM));
    if (late.address != early_cycle.address || late.read != early_cycle.read) {
        failed = true;
        a2ext_slot_disable();
        return;
    }
    if (gpio_get(A2EXT_GPIO_RES_N)) {
        bool selected = a2ext_slot_selected(&policy, &late);
        if (!late.read && selected) {
            uint8_t unused = 0;
            a2ext_latch_cycle(&late);
            (void)slot_handler(&late, &unused);
        } else if (late.read) {
            try_read();
        }
    }
    pending = false;
}
