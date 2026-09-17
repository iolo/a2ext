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

Enable the experimental responder with `a2ext_slot_enable(handler)` on the
bus core, then call `a2ext_slot_poll()` continuously there. It owns PIO2 SM0
(27 words) and PIO0 SM1 (a separate 3-word delayed sample). The handler sees
selected reads early and writes after the delayed sample. Return true with
`*reply` set to answer a read; false leaves the data bus released. The default
remains passive. Disable releases the data pads before stopping either SM.

`try_putdata` accepts requests only inside an eligible read callback, with
PHI0 and reset high. Acceptance means queued, not acknowledged by the 6502.
PIO matches a 24-bit cycle tag and rejects stale replies. C800 requires prior
local Cnxx selection; CFFF or another slot's Cnxx access releases ownership.
FIFO overflow or early/late address mismatch disables responses and latches
`slot_faulted`; re-enable explicitly to recover. Do not stop a core or PIO with
a debugger while connected to a running host.

This is an experimental response implementation: software tests do not prove
6502 setup/hold timing. Falling PHI0 can race the final enable instructions;
logical release takes up to four PIO cycles after the internally observed
edge, plus input synchronization and board propagation. Reset prevents new
CPU requests but does not asynchronously cancel an already queued reply.
Callbacks may have side effects even when their reply misses the deadline;
protocols needing acknowledged reads need a completion mechanism. Qualify
these limitations with a bus fixture before enabling active mode on a host.

## Optional shadow model

`a2ext_shadow.h` owns 128 KiB RAM plus 16 KiB validity. Select IIe or II/II+
explicitly at initialization. Feed each cycle and capture epoch from the capture
core; do not also apply deferred reset callbacks. /RES is sampled with each
cycle. Reset retains observed RAM but marks switches unknown until accesses
reacquire them. Startup and stream loss similarly require switch reacquisition;
unknown-bank writes are discarded. This can delay a useful display until the
host initializes its switches and redraws. Reading RAM alone cannot recover it.

RAM writes below C000 are tracked. ALTZP controls 0000-01FF; AUXWRITE controls
0200-BFFF except 80STORE's page-1 text and HIRES-dependent graphics overrides.
80STORE suppresses displayed page 2. IIe 80COL/ALTCHAR/AN3 are tracked; II/II+
ignore these. Language-card RAM, RamWorks, IIc/IIgs extensions, and Videx are
not modeled. `shadow_byte` reports unknown bytes; `shadow_copy` substitutes zero.
Atomic readers can take a frame copy while capture continues, with possible
tearing. No API claims a coherent host framebuffer snapshot.

Banking reference: [Apple IIe Reference Manual, chapter 4](https://www.applelogic.org/files/AIIEREF.pdf).
