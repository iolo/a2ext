# a2ext-carrier schematic prototype

Open `a2ext-carrier.kicad_pro` in KiCad 10. Symbols are project-local and embedded
in the schematic. `BOM.csv` lists component values; footprints not yet specified
are deliberate because PCB layout is out of scope. `connections.json` is the
generated connectivity contract, checked against KiCad's exported netlist.

Revision 0.5 uses A4 landscape with 1.524 mm pin names, wire labels, and values;
pin numbers are 1.27 mm and references/notes are 1.778 mm. Symbols and notes
are rearranged for printing at actual size; electrical connections are unchanged.

**Status: schematic draft, not electrically qualified.** ERC checks connectivity,
not bus timing, power sequencing, module thermals, or Apple II compatibility.

## Module and connections

M1 represents both WeAct V1.0 headers. Pin numbers `H1.n` and `H2.n` refer to
the vendor schematic, not arbitrary carrier header numbering. Do not substitute
a Pico 2 or Clintech module. See the module drawing for orientation.

Prepare the module with power disconnected: remove R16 (KEY/GPIO23), R19
(LED/GPIO25), R14 (secondary chip select), and **on-module U2** (the vendor's
unidentified VBUS-to-5V power-path device). Leave secondary memory U7/R13/C23
unpopulated. Removing U2 disconnects USB VBUS from the module supply; do not
bridge its vacated input/output pads. Carrier D2 is removed and M1 H1.1 (VBUS)
is unconnected. Inspect and continuity-test these modifications. USB is for
data only and cannot power the prepared card.

J1 follows the PRD's counter-clockwise slot numbering. /INT and /DMA chains
pass through. Unused negative supplies, +12V, /RDY, /DMA, /INH, and auxiliary
clocks are not connected. JP1 defaults open: close it only when motherboard
documentation confirms composite SYNC on slot 7 pin 19. UART0 and all 13 general
daughterboard GPIOs are on J2. /RES is sensed separately from module RUN.

## Direct bus and power

Revision 0.5 retains direct connections for all 33 bus signals to GPIO2-34,
with JP1 in the optional SYNC path. Wire labels use Apple II signal names
(`A0`, `D0`, `IOSEL_N`, etc.), `UART_TX`/`UART_RX`, and daughterboard names
such as `IDC03_GPIO35`. `_N` means active low; UART direction is from the
carrier's perspective. M1 shows the physical GPIO names and WeAct header
contacts; J2 shows pin functions alongside its contact numbers. Matching
wire labels identify the same electrical net. No bus switches, supervisors,
or BUS_GOOD/BUS_OE_N control circuit remain. GPIO40-47 stay on the 3.3 V
daughterboard interface. Firmware
must drive IRQ/NMI low or release them; the host supplies their pull-ups.

RP2350 fault-tolerant digital inputs support 5 V with IOVDD powered at 3.3 V.
The direct connection provides no protection against a live 5 V bus with an
unpowered module. All operating power comes from the slot supply. Flash with
the card removed from the host, using a 5 V fixture at J1 pins 25/26 and USB
for data only; do not hot-plug the card. Measure startup/shutdown
and brownout behavior using the [power-validation procedure](POWER-VALIDATION.md).

R4 retains the module RUN pull-up. RUN resets M1 but does not disconnect bus
pins; Apple /RES remains a separate input.

The power path is `J1.25 (+5V_SLOT) -> F1 -> D1 -> VSYS -> M1 H1.2`.
The WeAct module labels H1.2 **5V**; it feeds the regulator input and serves the
same function as Pico's VSYS. H1.1 is **VBUS**, and stays unconnected on the
carrier. D1 is retained as reverse-current protection, with its anode toward
F1 and cathode toward VSYS. C9 decouples VSYS. F2 feeds +5V_DB from the fused
slot rail before D1. J2 power pins are outputs, not auxiliary inputs.

Initial allocation: at most 400 mA for carrier/module plus 100 mA for the
daughterboard from the slot branch, subject to the actual host's available
budget and PTC derating. This is a design ceiling, not a measured consumption
or a fuse trip-current guarantee. The module regulator's part number/current
rating is unspecified in the vendor drawing; reserve the 3.3 V daughterboard
pin for light loads until that rating and module temperature are established.

## Checks and outstanding work

```sh
python3 tools/pinout.py
python3 tools/check_schematics.py a2ext-carrier
```

Run from the repository root. Regenerate explicitly with
`python3 tools/schematics.py carrier`; review changes before replacing manual
edits. Export the PDF with `kicad-cli sch export pdf`.

Physical release requires power-transition, supply/thermal, and bus timing
measurements. ERC does not establish the WeAct module's supply ramp behavior.

Sources: vendor module files in `ref/WeActStudio.RP2350BCoreBoard/HDK/`,
[RP2350 datasheet](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
