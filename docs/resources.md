# RP2350B resource and timing contract

Pin assignments originate in `hw/pinout.json`; run `python3 tools/pinout.py`
to check the generated firmware header. Use Pico SDK 2.2.0 (commit
`a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`) for the initial implementation.

## Resource allocation

| Function | PIO/base | State machines | Program words | DMA channels |
|---|---|---|---|---|
| Passive bus capture | PIO0 / 0 | SM0 | 3 of 32 | 2 reserved for alternating blocks |
| VGA (exclusive with DVI) | PIO1 / 16 | SM0-2 | 28 of 32 from reference | 1 |
| DVI (exclusive with VGA) | PIO1 / 16 | SM0-2 | 2 shared words at origin 0 | 6 (3 data, 3 control) |
| Active slot responder | PIO2 / 0 | SM0 | 27 of 32 | CPU FIFO service |
| Active delayed write sample | PIO0 / 0 | SM1 | 3 additional words | CPU FIFO service |

The passive and video programs can coexist without shared instruction memory,
state machines, or pins. The active responder assembles to 27 words; its instruction-level regression
checks cycle tags and release logic, but physical response timing is unproven.
The RP2350 has 16 DMA channels; reserve at most 8 for capture plus DVI. Claim
channels through the SDK, not hard-coded channel numbers. Use DMA IRQ0 for
video and IRQ1 for capture; the bundled video implementations use exclusive
handlers. GPIO/UART handlers and deferred callbacks run on core 0; core 1 owns
bus consumption and optional active responses. Renderer work runs on core 0.

Initialize each PIO's GPIO base before adding programs. GPIO35-45 video outputs
are in PIO1's GPIO16-47 window. Use the SDK's 64-bit mask APIs and `1ull << pin`
for high GPIOs; the reference DVI helpers' `3u << data_pins` are not valid for
these assignments. SDK pin configuration functions accept physical GPIO numbers;
PIO instruction immediate GPIO operands must respect the PIO base.

DVI clock GPIO42/43 is an even/odd pair on one PWM slice; reserve that slice
for the pixel clock. PIO produces the three TMDS data pairs. HSTX is not used:
its fixed GPIO range conflicts with the bus assignment. UART0 uses GPIO0/1;
never configure the module's default LED/button GPIOs.

## Capture timing and capacity

`a2ext_capture` waits for PHI0 low then high and samples GPIO2-29 after the
29-cycle delay. At a 126 MHz SM clock, the sample is approximately 32 SM clocks
(254 ns) after the observed external edge, allowing for input synchronization.
This follows the direct-capture reference's write-data sampling window; scope
measurements must account for added bus isolation propagation and host model.
Do not disable input synchronizers until measured timing justifies it.

The 28-bit word is shifted left and autopushed: bits 0-15 address, 16-23 data,
24 RWB, 25 /DEVSEL, 26 /IOSEL, 27 /IOSTRB. Select bits are active low. Capture
every PHI0 CPU cycle, not only slot-selected traffic. Read-cycle data is not
guaranteed valid at this sample instant; writes and read-side soft-switch
addresses are sufficient for the initial shadow model.

At a design budget of 1.1 million cycles/s, DMA traffic is 4.4 MB/s. Reserve
two 1024-word blocks (8 KiB), allowing about 0.93 ms per block. Joined RX FIFO
holds 8 words, only about 7.3 us at that rate: block DMA must chain without a
CPU rearm gap. FIFO stalls and unconsumed block reuse must both invalidate
shadow state; neither is recoverable by silently continuing the old stream.

Use a 126 MHz capture SM clock: divider 1 for 126 MHz demo/VGA and divider 2
for a 252 MHz DVI system clock. DVI's 252 MHz clock is above the RP2350's
150 MHz rating and remains an explicit experimental configuration requiring
physical qualification; do not raise the core voltage without a separate
documented rating review. If the clock cannot be established, remain passive
and report failure rather than changing timing silently.

## Memory envelope and remaining timing gate

Reserve 128 KiB for main/auxiliary shadow memory, 16 KiB for byte-validity maps,
8 KiB for capture blocks, and at most 32 KiB for video scanline/TMDS buffers.
Keep code, stacks, queues, and other data within the remaining SRAM verified
by linker maps; do not allocate a full 640x480 RGB framebuffer. Firmware
builds must report actual RAM usage rather than treating this budget as proof.

The delayed passive capture cannot serve slot reads on its own. PIO2 needs an
earlier request path, an explicit deadline, and a cycle identity so late CPU
responses cannot drive the following cycle. Gate outputs with read/selection,
PHI0, reset, and C800 ownership. There is no physical response-timing claim
until step 14's implementation and the hardware procedure pass.

Sources: bundled `ref/AppleII-VGA-rallepalaveev/pico/vga.pio`,
`ref/A2DVI-Firmware/libraries/libdvi/dvi_serialiser.pio` and `dvi.c`, and the
[RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
