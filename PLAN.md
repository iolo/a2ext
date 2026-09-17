# a2ext implementation plan

**Execution rule:** After each numbered implementation step, update `PROGRESS.md`
with changes, validation results, and blockers, then commit that step's changes
together with the progress update. Include only task-related changes. Record
partial or blocked work honestly; a commit does not imply completion.

## Summary and agreed scope

Build a WeAct Studio RP2350B Core Board carrier, VGA and DVI daughterboard
schematics, a shared firmware library, and demo/VGA/DVI firmware.

Target Apple II/II+ and IIe, including IIe auxiliary-memory video modes. Deliver
KiCad schematics, BOMs, documentation, and reproducible firmware builds. PCB
routing and fabrication outputs are excluded; physical validation remains a
separately recorded acceptance gate.

Use the bundled reference projects as porting sources, preserving attribution
and licenses. Keep their source trees unchanged.

Approved revision (2026-09-17): use direct bus connections, following the
RP2350 reference designs. Remove the CB3T switches and their supervisors,
BUS_GOOD/OE control, and local support components. This supersedes the earlier
isolation refinement. Keep power-transition measurements and document installed
slot-only power operation. Revision 0.3 removes D2 and leaves module VBUS NC;
slot power feeds F1/D1 and H1.2 (5V, equivalent to VSYS). On-module U2 stays
removed to disable USB power. Off-host flashing uses fixture power and USB data.

## 1. Resolve the hardware and firmware contracts

1. Update the PRD to identify the WeAct module and correct its connector
   description using the supplied schematic and dimensions.
2. Correct RX on IDC pin 2, `TMDS` spelling, `uint8_t`, and the DVI framebuffer
   description. Add the demo firmware to the expected outputs.
3. Record removal of the module's GPIO23 button connection and GPIO25 LED load
   through R16/R19, as approved. Verify these designators against the actual
   module revision. Leave optional secondary flash/PSRAM unpopulated because
   its chip select shares GPIO0.
4. Establish this GPIO assignment:

   | Signals | GPIOs |
   |---|---|
   | UART TX / RX | 0 / 1 |
   | A0-A15 | 2-17 |
   | D0-D7 | 18-25 |
   | RWB | 26 |
   | /DEVSEL, /IOSEL, /IOSTRB | 27, 28, 29 |
   | PHI0, /RES | 30, 31 |
   | /IRQ, /NMI, optional composite SYNC | 32, 33, 34 |
   | Daughterboard general-purpose signals | 35-47 |

5. Define IDC pins 1/2 as TX/RX; pins 3-15 as GPIO35-47; pin 16 as an additional
   ground; pin 17 as 3.3 V; pin 18 as module RUN; pins 19/20 as protected
   5 V/ground. This provides 13 additional GPIOs, accounting for all 33 Apple II
   bus signals.
6. Allocate PIO0 to bus capture with GPIO base 0 and PIO1 to video with GPIO
   base 16. Reserve PIO2 for active slot responses. Validate instruction,
   state-machine, DMA, and timing budgets before completing the schematics.
   RP2350 PIO blocks address 32 GPIOs at a time through these base selections.

**Exit criterion:** one reviewed pin/resource table shared by schematics,
firmware constants, and documentation.

## 2. Complete the three hardware designs

7. Create the carrier under `hw/a2ext-carrier`:
   - Use project-local symbols for the WeAct module and correctly numbered
     Apple II slot.
   - Preserve interrupt/DMA chain connections and specified unused slot pins.
   - Keep Apple /RES sensing separate from module RUN.
   - Implement /IRQ and /NMI as assert-low/release outputs.
   - Document slot-only power, USB power disconnection, reverse-current protection,
     decoupling, and daughterboard power budgets.
8. Validate startup, shutdown and brownout behavior for the approved direct-bus
   circuit. Document the powered-IOVDD requirement and USB operating restrictions.
   Keep ADC-capable GPIO40-47 exclusively on the 3.3 V daughterboard interface.
   Do not declare hardware ready if sequencing remains unresolved.
9. Create the VGA schematic under `hw/a2ext-vga`:
   - Assign R0-R2 to GPIO35-37, G0-G2 to GPIO38-40, B0-B2 to GPIO41-43.
   - Assign HSYNC/VSYNC to GPIO44/45.
   - Implement the specified resistor DACs and sync resistors; calculate
     output levels into a 75 ohm termination.
10. Create the DVI schematic under `hw/a2ext-dvi`:
    - Assign D0 +/- to GPIO36/37, D1 +/- to GPIO38/39, D2 +/- to GPIO40/41,
      and clock +/- to GPIO42/43.
    - Use the reference's resistor-driven TMDS circuit and verify polarity
      against serializer configuration.
    - Keep audio, CEC, and EDID negotiation outside v1.
    - Document direct daughterboard mating as the baseline; ribbon-cable
      operation requires separate signal-integrity validation.

**Exit criterion:** all three schematics pass ERC with reviewed exceptions and
include BOMs, exported PDFs, connector tables, and assembly notes.

## 3. Implement the shared library and demo

11. Establish CMake/Pico SDK builds and a WeAct board definition. Pin dependency
    revisions and produce ELF, UF2, and map files for all three firmware
    targets. Place the common library in `fw/a2ext-lib`.
12. Implement passive capture first:
    - Sample full addresses, data, RWB, and slot selects using PHI0-qualified
      timing.
    - Transfer captured cycles through DMA into bounded buffers.
    - Expose overflow counters and mark shadow state invalid after capture
      loss.
    - Keep timing-critical capture independent of rendering and UART callbacks.
13. Define the library interfaces:
    - Preserve requested API names and correct their types.
    - Add an atomic bus-cycle interface containing address, data, direction,
      and selection flags; define getaddr/getdata against the same latched
      cycle.
    - Restrict putdata to an eligible, current slot-read transaction; reject
      late responses and release the bus at cycle end.
    - Default to passive mode; explicitly enable slot response handling.
    - Use UART0 at 115200, 8N1. Retain the requested receive callback signature,
      with the byte in its low eight bits.
    - Define SYNC callbacks as counting composite-sync pulses, not PHI0 cycles.
      Missing slot-7 SYNC must not prevent operation.
14. Add active slot responses and port the a2pico demo into `fw/a2ext-demo`.
    Exercise slot registers/ROM, reset reporting, UART, IRQ, and NMI. Enforce
    C800 ownership and CFFF release; /IOSTRB alone must not enable data output.
15. Implement optional shared video shadowing: main/auxiliary memory tracking,
    video soft switches, page selection, and reset state. Begin capture early,
    document incomplete initial shadow contents, and avoid clearing shadow RAM
    merely because Apple RESET occurs.

**Exit criterion:** demo builds and automated bus traces validate capture,
slot ownership, and shadow-state behavior.

## 4. Port VGA, then DVI

16. Port AppleII-VGA rendering into `fw/a2ext-vga`, replacing its bus interface
    with the common library. Start with test patterns, then add 40-column text,
    lores, hires, mixed mode, page switching, and IIe extended modes.
17. Port A2DVI-Firmware into `fw/a2ext-dvi`, retaining its renderer and PIO/libdvi
    serializer approach. Adapt GPIO-base handling and remove
    transceiver-specific capture code. Use the shared shadow model.
18. Default both outputs to 640x480 at approximately 60 Hz. Give bus capture
    priority over rendering and diagnostics. Document and validate the DVI
    clock configuration, including any above-rated operation inherited from
    the reference.

**Exit criterion:** both backends render the same replayed Apple II video states
without capture overflow or resource conflicts.

## 5. Verify and package

19. Automate clean builds, pin-allocation checks, KiCad ERC, and trace-based tests
    covering full-address capture, consecutive cycles, reset, overflow
    recovery, selected/unselected reads, late responses, C800 ownership,
    II/II+ video modes, IIe banking, 80-column, double-lores, double-hires,
    missing SYNC, and simultaneous capture/rendering load.
20. Publish hardware validation procedures for power sequencing, bus loading,
    response timing, interrupt release, VGA voltage/timing, and DVI stability.
21. Complete the README with build/flashing instructions, module modifications,
    compatibility matrix, resource allocation, upstream attribution, and
    validation results. Clearly distinguish automated verification from
    measurements requiring assembled hardware.

## Technical references

- Local module schematic, dimensions, and pinout:
  `ref/WeActStudio.RP2350BCoreBoard/HDK/`.
- [RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf):
  PIO GPIOBASE, electrical ratings, and GPIO pad types.
- [Raspberry Pi 5 V tolerance qualification](https://www.raspberrypi.com/news/rp2350-a4-rp2354-and-a-new-hacking-challenge/):
  IOVDD must remain powered when 5 V is applied to GPIO.
