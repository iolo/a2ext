# a2ext

Apple II extension-card prototype built around the **WeAct Studio RP2350B Core
Board V1.0**, with interchangeable VGA and DVI daughterboards. It captures the
full 16-bit address bus, shares a main/auxiliary RAM shadow between firmware
backends, and provides UART and an optional active slot-ROM demo.

**Status: implemented schematic and firmware prototypes; hardware acceptance is
open.** Software tests and all three schematic ERC checks pass. Power sequencing,
bus timing, live capture throughput and monitor operation have not been measured.
DVI and the active demo use experimental 252 MHz clocking, above the RP2350
rating. PCB layout and fabrication files are outside this release.

## Deliverables

| Component | Files |
|---|---|
| Carrier with direct Apple II bus connections | [KiCad project, PDF, BOM and assembly notes](hw/a2ext-carrier/) |
| RGB333 VGA daughterboard | [KiCad project, PDF, BOM and DAC calculations](hw/a2ext-vga/) |
| DVI over HDMI connector | [KiCad project, PDF, BOM and wiring](hw/a2ext-dvi/) |
| Common capture, API and shadow library | [a2ext-lib](fw/a2ext-lib/README.md) |
| Passive/active demonstration | [a2ext-demo](fw/a2ext-demo/README.md) |
| AppleII-VGA renderer port | [a2ext-vga](fw/a2ext-vga/README.md) |
| A2DVI renderer/libdvi port | [a2ext-dvi](fw/a2ext-dvi/README.md) |

[PRD](PRD.md), [implementation plan](PLAN.md), and [progress record](PROGRESS.md)
describe the scope and per-step commits. [GPIO/IDC assignments](hw/pinout.json)
are the shared hardware/firmware pin contract.

## Build and verify

Use Pico SDK/picotool 2.2.0, ARM GCC/newlib and CMake. The active demo additionally
requires ca65/ld65. See [firmware build instructions](fw/README.md) for dependency
revisions, configuration options and flashing.

```sh
cmake -S . -B build/local -DPICO_SDK_PATH=/path/to/pico-sdk \
  -DPICO_TOOLCHAIN_PATH=/path/to/arm-toolchain -DCMAKE_BUILD_TYPE=Release
cmake --build build/local -j4
python3 tools/smoke.py
python3 tools/smoke.py --erc --firmware-from build/local
```

Builds produce `a2ext-demo`, `a2ext-vga` and `a2ext-dvi` ELF/UF2/map files.
The default demo is passive; video targets render host shadow memory at nominal
640x480/60 Hz. `A2EXT_APPLE_MODEL=IIPLUS` selects II/II+ behavior;
`A2EXT_VIDEO_TEST_PATTERN=ON` selects video test patterns;
`A2EXT_DEMO_ACTIVE=ON` opts into the experimental slot responder.

The [verification record](docs/VERIFICATION.md) separates host replay, clean
builds and ERC from unperformed physical tests. Renderer replay writes images
to `build/replay`. [Resource accounting](docs/resources.md) covers PIO, DMA,
clocking, scheduling and SRAM; no full output framebuffer is allocated.

## Hardware preparation and first use

The module has **two 2x15 headers**, not Pico headers. With all power removed,
prepare its GPIO23 button, GPIO25 LED, secondary-memory branch and USB power path:
remove **R16, R19, R14 when fitted, and on-module U2**; leave U7/R13/C23
unpopulated. U2 removal disables USB power; carrier D2 is omitted. Read the
[carrier assembly notes](hw/a2ext-carrier/README.md) before modifying a module;
on-module designators differ from carrier designators.

All 33 host-bus lines connect directly to GPIO2-34, with an optional SYNC jumper.
GPIO40-47 remain on the 3.3 V daughterboard interface. There is no power-off bus
isolation. Slot pin 25 feeds F1/D1 and the module's **5V (H1.2)** input,
labelled `VSYS` on the carrier; **VBUS (H1.1)** is unconnected. USB is data only.
For flashing, remove the card and supply 5 V through a fixture at slot pins
25/26. Do not hot-plug it. The
[power-transition checks](hw/a2ext-carrier/POWER-VALIDATION.md) and
[bench procedure](docs/HARDWARE-VALIDATION.md) remain open.
Use direct daughterboard mating first. The fused slot rail supplies HDMI +5 V.

UART0 is 115200 8N1, 3.3 V, on IDC pins 1 (TX) and 2 (RX), with ground on 16/20.
Send `?` for passive/video diagnostics. Missing slot-7 SYNC does not gate video.
Capture begins before renderer initialization, but it cannot reconstruct earlier
RAM writes. Unknown bank state requires explicit switch initialization and a host
redraw; warm RESET preserves RAM and reacquires switches. The bench guide gives
a repeatable IIe initialization sequence. Active response limitations, including
late replies and reset races, are documented in the library and demo guides.

## Compatibility scope

| Host/output | Implemented software | Validation |
|---|---|---|
| Apple II / II+ | 40-column normal/inverse/flashing text, lores, hires, mixed, pages 1/2 | Host replay and builds; physical not run |
| Apple IIe | Above plus main/aux banking, 80-column, alternate charset, double lores/hires, 80STORE and IOUDIS | Host replay and builds; physical not run |
| VGA | RGB333, 640x480/60, 126 MHz system clock | Replay/build/ERC; DAC/sync/monitor not run |
| DVI | TMDS via PIO1/PWM, 640x480/60, experimental 252 MHz | Replay/build/ERC; signal/clock/monitor not run |
| Active demo | Slot registers/ROM, C800 ownership, UART, IRQ/NMI | Policy/PIO logic/build; physical timing not run |

US enhanced IIe and US II/II+ fonts are bundled. Unenhanced IIe-specific font,
PAL color emulation, Videx/Video7 interfaces, IIc/IIgs, language-card/RamWorks
shadowing, audio, CEC and EDID negotiation are outside the validated scope.
The two video renderers retain their upstream artifact-color palettes.

## Upstream work

This project adapts [a2pico](https://github.com/oliverschmidt/a2pico),
[AppleII-VGA](https://github.com/markadev/AppleII-VGA) through the
[rallepalaveev fork](https://github.com/rallepalaveev/AppleII-VGA), and
[A2DVI-Firmware](https://github.com/ThorstenBr/A2DVI-Firmware), including libdvi.
Original MIT notices are retained alongside the ports. See
[attribution and revisions](docs/ATTRIBUTION.md). Reference trees are kept
separate from the adapted firmware sources.
