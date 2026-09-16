# a2ext-lib interface

Call `a2ext_init()` once on core 0 before starting capture or other cores. It
releases every Apple II bus pin, initializes UART0 at 115200 8N1, and enables
reset observation. It never configures a default LED or button. Active data
output is disabled by default.

Call capture start/next/stop/stats on one owning core (normally core 1). The
capture engine owns PIO0 SM0, two claimed DMA channels, and DMA IRQ1 on that
core. `a2ext_next_cycle` is nonblocking and returns an atomic address/data/RWB/
select sample. Select booleans mean asserted. Read-cycle data is observational
only; the current sampling window guarantees no claim about CPU read values.

`getaddr/getdata` return fields of the last successfully returned cycle; they
do not consume or read live GPIOs. `has_cycle` is false before the first sample.
Prefer the atomic cycle interface. Getters belong to the capture owner, not
arbitrary concurrent consumers. Watch `stats.epoch`: start, stop, FIFO stalls,
and unread-block overwrite break continuity. Overflow recovery discards queued
samples and resynchronizes on PHI0; shadow users must invalidate their state.

`irq(true)` and `nmi(true)` assert low; false releases the line. The output
latch is always zero. Apple reset assertion releases both interrupt outputs.
The carrier's switch isolation and host pull-ups complete this interface.

Register reset, UART receive, and optional composite SYNC callbacks on core 0.
Call `a2ext_poll` there regularly. IRQs enqueue events; poll dispatches at most
32 per call. The bounded queue counts dropped events via `callback_drops`.
Callback loss must be reported by the application. Callbacks never run in
capture context, and must not perform long blocking work when rendering video.

SYNC is slot-7 composite sync, not the CPU clock. Registration counts falling
edges; counter 0 or NULL disables it. An absent SYNC signal does not affect
capture or video timing. Reset callbacks receive true on assertion and false
on release. UART receive passes a byte zero-extended to the requested uint32_t
callback argument. `send` blocks until UART TX accepts a byte; do not call it
from the capture/response core.

At API-definition stage `try_putdata` rejects all writes and `putdata` wraps it.
The bounded active-slot transaction path is step 14 work; this deliberately
does not expose an unrestricted GPIO data-bus write.
