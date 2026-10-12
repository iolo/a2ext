# Two-layer prototype fabrication and assembly

Revision PCB-P1, 2026-10-12. All three boards preserve the existing electrical
contracts. KiCad 10.0.7 ERC, DRC including warnings/exclusions, schematic parity,
and physical pad-to-net checks pass with zero findings. The power, timing,
thermal and monitor tests in [HARDWARE-VALIDATION.md](../docs/HARDWARE-VALIDATION.md)
remain open. These files are for prototype fabrication.

## Deliverables

| Board | Outline dimensions | Editable board | Fabrication ZIP |
|---|---|---|---|
| Carrier | 99.695 x 78.74 mm including tab | [KiCad PCB](a2ext-carrier/a2ext-carrier.kicad_pcb) | [Gerbers/drills](a2ext-carrier/a2ext-carrier-gerbers.zip) |
| VGA | 45 x 45 mm | [KiCad PCB](a2ext-vga/a2ext-vga.kicad_pcb) | [Gerbers/drills](a2ext-vga/a2ext-vga-gerbers.zip) |
| DVI | 45 x 45 mm | [KiCad PCB](a2ext-dvi/a2ext-dvi.kicad_pcb) | [Gerbers/drills](a2ext-dvi/a2ext-dvi-gerbers.zip) |

Each ZIP contains top/bottom copper, mask, silk and paste Gerbers, a closed
outline, a Gerber job file and separate plated/nonplated Excellon drills.
Copper and drills share the absolute origin. Do not mirror or rescale them.
Paste layers support stencil ordering; the underside paste is empty.
Open each `.kicad_pro` beside its board and retain the shared `a2ext.pretty`
library. `previews/` contains top/bottom layer plots and an assembly plot with
pad numbers; bottom plots show the view from the underside. `previews/`
also includes `gerber-top.png` and `gerber-bottom.png`, rendered from the actual
exported copper, mask, silk and drill geometry. `validation/`
contains ERC/DRC results, routed lengths, drill reports and SHA256 checksums of
the exported PCB, schematic and fabrication files.

![PCB overview](pcb-overview.png)

## Fabricator instructions

| Parameter | Specification |
|---|---|
| Stack | Two layers, FR-4, nominal 1.6 mm finished thickness |
| Copper | 35 um / 1 oz finished copper on each side |
| Traces | 0.25 mm nominal; 0.15 mm minimum neck/fanout; 0.50 mm slot-power routing |
| Clearance | 0.15 mm minimum; ground pours 0.20 mm |
| Vias | 0.60 mm pad / 0.30 mm finished plated drill |
| Mask / silk | Both sides, as supplied |
| Daughterboard finish | ENIG |
| Carrier finish | Selective hard gold on both sets of 25 contacts; ENIG elsewhere |
| Carrier insertion edge | 45 degree bevel on both faces; maximum 1.0 mm setback from the bottom outline |
| Profile | Edge.Cuts; no panelization or breakaway tabs included |

Quote the hard-gold process and bevel explicitly; these instructions are not
encoded in Gerber copper. Fingers are 1.778 x 7.62 mm on 2.54 mm pitch, ending
1.27 mm above the bottom edge. The tab is 66.04 mm wide and projects 10.16 mm
below the shoulders. It contains no paste or ground pour. Check finished
thickness against the actual host slot before inserting an assembled card.

## Footprints and component selection

| References | Physical implementation |
|---|---|
| Carrier J1 | 50-contact Apple II edge; pins 1-25 component side, 50-26 opposite |
| Carrier M1 | Prepared WeAct RP2350B V1.0; two top-mounted 2x15, 2.54 mm female sockets |
| Carrier J2 | Top-mounted shrouded male IDC20, 2x10, 2.54 mm |
| VGA/DVI J1 | **Bottom-mounted** vertical 2x10, 2.54 mm female socket |
| VGA J2 | Right-angle female DE-15HD, 2.29 x 1.90 mm signal pitch, 25 mm shell-hole spacing, 3.03 mm edge-pin offset / 4.94 mm shell-hole-to-edge offset |
| DVI J2 | **Molex 208658-1001** HDMI Type A; four shell contacts on SH/GND |
| Carrier D1 | SS14 in SMA / DO-214AC; pad 1 cathode, pad 2 anode |
| Carrier F1/F2 | 1206 PTC, 500 mA / 100 mA hold respectively; check chosen land pattern and derating |
| Carrier R4; VGA resistors | 0805; VGA resistors 1% |
| DVI resistors | 0402, 270 ohm, 1%; reflow or microscope-assisted assembly |
| Carrier C8 / DVI C1 | 0805, 100 nF ceramic |
| Carrier C9/C10 | 1206, 10 uF ceramic, at least 10 V; account for DC-bias derating |
| Carrier JP1 | 1x2, 2.54 mm; leave open unless slot-7 SYNC is verified |
| PCB H references | 2.7 mm nonplated holes for M2.5 hardware |

Compare the VGA connector manufacturer's drawing to the local footprint before
purchasing. A generic DE-15 part description is insufficient. The DVI
schematic's generic HDMI-SWM-19 label does not specify the physical supplier
part for this PCB; use the Molex connector above.

## Assembly and mating

1. Populate carrier SMD parts and check D1 polarity. Prepare the module as in
   [carrier notes](a2ext-carrier/README.md), including USB power-path U2 removal.
   Install the module sockets and module.
2. Populate daughterboard top-side parts and video connector. Fit J1 on the
   **underside**, with its square pin-1 pad mating to carrier J2 pin 1.
3. Select matching socket/header heights that fully engage without housing
   interference. The footprints specify holes, not a manufacturer-specific
   mating stack height. Fit matching M2.5 spacers at H1/H2 to support connector
   loads. PCB H1/H2 are separate from the WeAct module's H1/H2 header names.
4. Daughterboard coordinates translate +65 mm in X, unchanged Y, onto the
   carrier; all 20 contacts and both spacer holes align. A daughterboard
   extends 25.305 mm past the carrier edge. Check lid, rear opening and
   neighboring-card clearance using actual connector and socket heights.
5. Continuity-test supplies and grounds. Start with the off-host slot-power
   fixture and physical validation procedure. USB is data only. Begin with
   direct daughterboard mating.

M1 follows the vendor top view: H2 is the upper header, H1 the lower. Outer rows
are 38.1 mm apart, columns use 2.54 mm pitch, and the body outline measures
41.402 x 41.148 mm. Socket polarity and physical fit still require inspection
on actual parts.

## DVI routing and physical acceptance

Resistor-to-HDMI pairs use F.Cu without vias, with approximately 8.3-9.3 mm trace
lengths and below 0.083 mm intra-pair length difference. B.Cu provides ground
beneath those fanouts. Carrier and IDC-to-resistor paths use the fixed pin map
and are not pair-length tuned or impedance controlled; complete net lengths
are in the validation summaries. Two-layer FR-4 and the reference's resistor
drive are experimental. DRC does not establish eye quality, HDMI compliance
or stable operation at the firmware's experimental 252 MHz clock.

## Reproduction

```sh
python3 tools/check_schematics.py a2ext-carrier a2ext-vga a2ext-dvi
/usr/bin/python3 tools/check_pcbs.py --export
```

The second command refills pours, requires zero ERC/DRC/parity findings, checks
pad contracts and mating geometry, and exports fabrication packages.
`tools/pcbs.py` explicitly regenerates placement and DSN files and **replaces
routed PCBs**. Preserve manual work before running:

```sh
/usr/bin/python3 tools/pcbs.py
# Run Freerouting 2.5.0 for each board, for example:
java -Djava.awt.headless=true -jar /path/to/freerouting-2.5.0.jar \
  --gui.enabled=false --user_data_path=/tmp/a2ext-router -da \
  -de build/pcb/a2ext-carrier/a2ext-carrier.dsn \
  -do build/pcb/a2ext-carrier/a2ext-carrier.ses -mt 1 -mp 20
# Repeat for a2ext-vga and a2ext-dvi before importing all sessions.
/usr/bin/python3 tools/pcbs.py --import-session build/pcb
/usr/bin/python3 tools/pcbs.py --finish
/usr/bin/python3 tools/check_pcbs.py --export
```

DSN clearances and widths are written explicitly because standalone pcbnew
does not load project net classes during export. The final check accepts no
design-rule exceptions.

## Sources

- [Tebl compact Apple II prototyping card](https://github.com/tebl/Apple2-Prototyping-Card/tree/master/small), revision `91ed325a28d3013bd6c6971858b9d634d92732c9`: measured envelope, tab and contact geometry, drawn for this project.
- WeAct V1.0 mechanical and pin drawings in `ref/WeActStudio.RP2350BCoreBoard/HDK/`.
- KiCad 10 footprints: attribution and retained license in [a2ext.pretty/README.md](a2ext.pretty/README.md).
- [Freerouting CLI documentation](https://github.com/freerouting/freerouting/blob/master/docs/command_line_arguments.md), used with version 2.5.0.
