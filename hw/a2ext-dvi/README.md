# a2ext-dvi

Revision 0.2 uses A4 landscape with enlarged text: 1.524 mm pin names,
wire labels and values, 1.27 mm pin numbers, and 1.778 mm references/notes.
The revised layout preserves all electrical connections.

Passive DVI video daughterboard using an HDMI Type A connector and the PRD's
270 ohm series resistor network. Open the KiCad 10 project; symbols are local.
The abstract SH pin represents all connector shell contacts. Confirm the exact
HDMI-SWM-19 mechanical drawing and pad numbering before any PCB work.

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
