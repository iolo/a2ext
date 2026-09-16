# a2ext-carrier schematic prototype

Open `a2ext-carrier.kicad_pro` in KiCad 10. Symbols are project-local and embedded
in the schematic. `BOM.csv` lists component values; footprints not yet specified
are deliberate because PCB layout is out of scope. `connections.json` is the
generated connectivity contract, checked against KiCad's exported netlist.

**Status: schematic draft, not electrically qualified.** ERC checks connectivity,
not bus timing, power sequencing, module thermals, or Apple II compatibility.

## Module and connections

M1 represents both WeAct V1.0 headers. Pin numbers `H1.n` and `H2.n` refer to
the vendor schematic, not arbitrary carrier header numbering. Do not substitute
a Pico 2 or Clintech module. See the module drawing for orientation.

Prepare the module with power disconnected: remove R16 (KEY/GPIO23), R19
(LED/GPIO25), R14 (secondary chip select), and **on-module U2** (the vendor's
unidentified VBUS-to-5V power-path device). Leave secondary memory U7/R13/C23
unpopulated. Carrier D2 replaces the U2 power path through the exposed VBUS/5V
contacts, so USB power remains available. These on-module designators differ
from the carrier's U2, which is a required bus switch. Inspect and continuity
test the prepared module; do not bridge the vacated U2 input/output pads.

J1 follows the PRD's counter-clockwise slot numbering. /INT and /DMA chains
pass through. Unused negative supplies, +12V, /RDY, /DMA, /INH, and auxiliary
clocks are not connected. JP1 defaults open: close it only when motherboard
documentation confirms composite SYNC on slot 7 pin 19. UART0 and all 13 general
daughterboard GPIOs are on J2. /RES is sensed separately from module RUN.

## Isolation and power

Five SN74CB3T3245PWR switches route all 33 bus signals, including the
bidirectional data bus and open-drain interrupt lines. They do not multiplex
signals or require GPIO direction controls. Use the **CB3T** variant: its high
output level follows its 3.3 V supply. A CB3Q variant passes higher levels and
is not an equivalent substitute. Firmware must drive IRQ/NMI low or release
them, never actively drive high; rely on host pull-ups across the switches.

All OE inputs share a 4.7 kohm pull-up to 3.3 V, defaulting to isolation. U6
monitors module 3.3 V; U7 monitors raw slot 5 V while powered from module 3.3 V.
Their open-drain reset outputs combine on BUS_GOOD. Q1 pulls OE low only after
both outputs release, with a nominal 20 ms supervisor delay. Module RUN low
asserts both supervisors' manual-reset inputs. Apple /RES does not reset M1.

F1 limits the slot-powered carrier branch. D1 and D2 diode-OR slot power and
USB VBUS into the module's 5V contact after removing on-module U2. F2 limits the
daughterboard's separate raw slot-derived +5V_DB output. That output is absent
on USB-only bench power; USB-only DVI monitor detection is therefore not a
supported test configuration. J2 power pins are outputs, not auxiliary inputs.

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

Physical release requires the power-sequencing procedure, supply/thermal
measurements, and bus timing tests. In particular, supervisor response and
switch behavior during a rapid module brownout cannot be established by ERC.

Sources: vendor module files in `ref/WeActStudio.RP2350BCoreBoard/HDK/`,
[TI CB3T3245 datasheet](https://www.ti.com/lit/ds/symlink/sn74cb3t3245.pdf), and
[TI TPS3808 datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf).
