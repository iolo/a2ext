#include "a2ext.h"
#include "a2ext_pins.h"
#include "hardware/gpio.h"
#include "hardware/irq.h"
#include "hardware/sync.h"
#include "hardware/uart.h"
#include "a2ext_internal.h"

enum { EVENT_RX, EVENT_RESET, EVENT_SYNC, EVENT_COUNT = 128 };
typedef struct { uint8_t kind, data; } event_t;
static event_t events[EVENT_COUNT];
static volatile unsigned event_head, event_tail;
static volatile uint32_t drops;
static void (*reset_handler)(bool);
static void (*sync_handler)(void);
static void (*receive_handler)(uint32_t);
static uint32_t sync_period, sync_edges;
static a2ext_cycle_t latched_cycle;
static bool has_cycle;

static void enqueue(unsigned kind, unsigned data) {
    /* UART and GPIO IRQs use equal priority on the same core. */
    unsigned next = (event_head + 1u) % EVENT_COUNT;
    if (next == event_tail) { ++drops; return; }
    events[event_head] = (event_t){(uint8_t)kind, (uint8_t)data};
    __dmb();
    event_head = next;
}

static void uart_handler(void) {
    while (uart_is_readable(uart0)) enqueue(EVENT_RX, uart_getc(uart0));
}

static void gpio_handler(unsigned gpio, uint32_t flags) {
    if (gpio == A2EXT_GPIO_RES_N) {
        if (flags & GPIO_IRQ_EDGE_FALL) {
            a2ext_irq(false);
            a2ext_nmi(false);
            enqueue(EVENT_RESET, true);
        }
        if (flags & GPIO_IRQ_EDGE_RISE) enqueue(EVENT_RESET, false);
    } else if (gpio == A2EXT_GPIO_SYNC && sync_period &&
               (flags & GPIO_IRQ_EDGE_FALL) && ++sync_edges == sync_period) {
        sync_edges = 0;
        enqueue(EVENT_SYNC, 0);
    }
}

void a2ext_init(void) {
    for (unsigned pin = A2EXT_GPIO_A0; pin <= A2EXT_GPIO_SYNC; ++pin) {
        gpio_init(pin);
        gpio_disable_pulls(pin);
        gpio_put(pin, false);
        gpio_set_dir(pin, GPIO_IN);
    }
    uart_init(uart0, 115200);
    uart_set_format(uart0, 8, 1, UART_PARITY_NONE);
    uart_set_hw_flow(uart0, false, false);
    gpio_set_function(A2EXT_GPIO_UART_TX, GPIO_FUNC_UART);
    gpio_set_function(A2EXT_GPIO_UART_RX, GPIO_FUNC_UART);
    gpio_pull_up(A2EXT_GPIO_UART_RX);
    irq_set_exclusive_handler(UART0_IRQ, uart_handler);
    irq_set_enabled(UART0_IRQ, true);
    uart_set_irq_enables(uart0, true, false);
    gpio_set_irq_enabled_with_callback(A2EXT_GPIO_RES_N,
        GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, true, gpio_handler);
}

void a2ext_latch_cycle(const a2ext_cycle_t *cycle) { latched_cycle = *cycle; has_cycle = true; }
bool a2ext_has_cycle(void) { return has_cycle; }
uint16_t a2ext_getaddr(void) { return latched_cycle.address; }
uint8_t a2ext_getdata(void) { return latched_cycle.data; }

void a2ext_putdata(uint8_t data) { (void)a2ext_try_putdata(data); }

static void open_drain(unsigned pin, bool asserted) {
    gpio_put(pin, false);
    gpio_set_dir(pin, asserted ? GPIO_OUT : GPIO_IN);
}
void a2ext_irq(bool on) { open_drain(A2EXT_GPIO_IRQ_N, on); }
void a2ext_nmi(bool on) { open_drain(A2EXT_GPIO_NMI_N, on); }
void a2ext_send(uint8_t data) { uart_putc_raw(uart0, data); }
bool a2ext_try_send(uint8_t data) {
    if (!uart_is_writable(uart0)) return false;
    uart_putc_raw(uart0, data);
    return true;
}
void a2ext_on_reset(void (*handler)(bool)) { reset_handler = handler; }
void a2ext_on_receive(void (*handler)(uint32_t)) { receive_handler = handler; }

void a2ext_on_sync(void (*handler)(void), uint32_t counter) {
    uint32_t saved = save_and_disable_interrupts();
    gpio_set_irq_enabled(A2EXT_GPIO_SYNC, GPIO_IRQ_EDGE_FALL, false);
    gpio_acknowledge_irq(A2EXT_GPIO_SYNC, GPIO_IRQ_EDGE_FALL);
    sync_handler = handler;
    sync_period = handler ? counter : 0;
    sync_edges = 0;
    if (sync_period) gpio_set_irq_enabled(A2EXT_GPIO_SYNC, GPIO_IRQ_EDGE_FALL, true);
    restore_interrupts(saved);
}

void a2ext_poll(void) {
    /* Bound callback work so callers can schedule video rendering. */
    for (unsigned count = 0; count < 32; ++count) {
        uint32_t saved = save_and_disable_interrupts();
        if (event_tail == event_head) { restore_interrupts(saved); break; }
        __dmb();
        event_t event = events[event_tail];
        event_tail = (event_tail + 1u) % EVENT_COUNT;
        restore_interrupts(saved);
        if (event.kind == EVENT_RX && receive_handler) receive_handler(event.data);
        if (event.kind == EVENT_RESET && reset_handler) reset_handler(event.data != 0);
        if (event.kind == EVENT_SYNC && sync_handler) sync_handler();
    }
}

uint32_t a2ext_callback_drops(void) { return drops; }
