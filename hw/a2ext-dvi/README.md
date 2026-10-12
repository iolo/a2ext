# a2ext-dvi

Revision 0.3 uses A4 landscape with enlarged text: 1.524 mm pin names,
wire labels and values, 1.27 mm pin numbers, and 1.778 mm references/notes.
The revised layout preserves all electrical connections.

Passive DVI video daughterboard using an HDMI Type A connector and the PRD's
270 ohm series resistor network. Open the KiCad 10 project; symbols are local.
The SH pin represents all four plated shell contacts. The physical PCB selects
**Kycon KDMIX-SL1-NS-WS-B15** for PCB-P2-THT. All 19 signal contacts and four
shell tabs are through-hole. This upright right-angle port exits the right
board edge; its approximately 16.4 mm body height and panel opening require a
new fit check. The PCB-P1 Molex connector cannot fit this revision.

The 45 x 45 mm two-layer board uses axial 1/4 W DIN0207 270 ohm resistors
(7.62 mm formed pitch), a 5.0 mm pitch radial ceramic capacitor,
and a bottom-mounted 2x10 female socket at J1. H1/H2 are 2.7 mm spacer holes
aligned with the carrier. Resistor-to-HDMI pairs use a single layer per pair
without vias: D0/D1 on F.Cu and D2/clock on B.Cu. Output tuning keeps
intra-pair trace-length difference below 0.020 mm. Full routed lengths are in
`validation/summary.json`; the carrier and IDC-to-resistor segments are not
pair-length tuned. Controlled impedance and physical signal quality are unqualified.
See [fabrication notes](../PCB-FABRICATION.md), [Gerbers and drills](a2ext-dvi-gerbers.zip),
[top](previews/top.svg), [bottom](previews/bottom.svg), and
[assembly](previews/assembly-top.svg) plots. DRC, ERC, and schematic parity
reports in `validation/` have zero findings.
No SMD assembly or solder stencil is required. All four shell tabs require
plated slots; retain both drill files when ordering.
`tmds-routing.json` preserves the reviewed pair tracks during regeneration;
the placement generator locks them before routing the other nets.

| Lane | Positive GPIO / IDC | Negative GPIO / IDC | HDMI contacts |
|---|---|---|---|
| D0 | 36 / 4 | 37 / 5 | 7 / 9 |
| D1 | 38 / 6 | 39 / 7 | 4 / 6 |
| D2 | 40 / 8 | 41 / 9 | 1 / 3 |
| Clock | 42 / 10 | 43 / 11 | 10 / 12 |

Each conductor has a 270 ohm, 1% resistor. Shields, pin 17, shell, and both IDC
ground contacts share GND. Pin 18 receives the carrier's fused +5V_DB supply;
there is no additional series diode drop on this board. C1 decouples that rail.
UART, RUN, 3.3 V power, GPIO35/44-47, DDC, HPD, CEC, and utility are unused.

The bundled libdvi program uses the lower GPIO for the positive conductor when
`invert_diffpairs=false`. Use PIO1 base 16 and 64-bit mask helpers. Its clock
generator uses the shared PWM slice for even/odd GPIO42/43. This is the
reference's resistor-driven signaling approach, not a claim of HDMI compliance.

Initially use direct carrier mating. No ribbon cable length is qualified.
Validate a fixed 640x480 timing mode, pair polarity, eye/edge quality, connector
+5 V, and lock on multiple monitors with a real board. No EDID negotiation or
hotplug handling is implemented by this schematic. Carrier power comes from
the slot input (or an off-host fixture at that input); USB is data only.

Validation so far: ERC and named-net export checks. Firmware and physical
TMDS tests are pending. From the repository root:

```sh
python3 tools/schematics.py dvi
python3 tools/check_schematics.py a2ext-dvi
```

References: `ref/A2DVI` v5.x hardware and
`ref/A2DVI-Firmware/libraries/libdvi/dvi_serialiser.{c,pio}`.
