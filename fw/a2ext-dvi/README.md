# DVI firmware

Port of the bundled A2DVI-Firmware renderer and its libdvi serializer. Original
MIT notices remain in the source, LICENSE, and libdvi/LICENSE. Text, lores,
hires, mixed, page switching, 80-column, double-lores and double-hires paths
consume frame copies from the common main/aux shadow model.

PIO1 base 16 drives the three TMDS data pairs, PWM GPIO42/43 drives the clock,
and six DMA channels feed the serializer through DMA IRQ0 on core 0. Core 1
owns passive bus capture. Output is 640x480 at 60 Hz, with 560x384 Apple content
and 48-line top/bottom borders. Eight 3840-byte TMDS buffers are allocated;
there is no full RGB framebuffer. No SYNC input or EDID negotiation is needed.

252 MHz is experimental and above the RP2350's rated frequency. Firmware does
not raise core voltage. Build success is not evidence of physical stability,
monitor lock, or reliable capture under rendering load. Qualification requires
the carrier power gate, timing measurements and sustained host/monitor tests.

`A2EXT_APPLE_MODEL=IIE` (default) uses an enhanced US font and IIe banking;
`IIPLUS` uses II/II+ behavior. `A2EXT_VIDEO_TEST_PATTERN=ON` produces color bars
while capture continues. UART `?` reports capture status. Menus, Videx, Video7,
IIgs, buttons/LEDs, custom configuration registers and alternate video timings
from the reference are outside this port's supported interface.

Adaptations: high-GPIO 64-bit masks, PIO base 16, carrier pair polarity, normal
Pico SDK RAM sections instead of the upstream custom linker-copy scheme,
384-line content window, fixed configuration, common capture/shadow, and
finite-frame entry point. TMDS patterns retain the upstream color choices;
VGA and DVI artifact colors need not be numerically identical.
