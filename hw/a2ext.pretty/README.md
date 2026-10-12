# a2ext physical footprint library

The KiCad 10 distribution footprint library provides the following local copies.
Copyright belongs to the KiCad library contributors. These redistributed
footprints and their modifications use CC-BY-SA 4.0 with KiCad's electronic-design
exception; the original [license document](LICENSE.md) is retained here.

| Local name | Original library / footprint |
|---|---|
| R_Axial_7.62 | Resistor_THT / R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal |
| C_Radial_5 | Capacitor_THT / C_Rect_L7.0mm_W4.5mm_P5.00mm |
| Schottky_DO41 | Diode_THT / D_DO-41_SOD81_P10.16mm_Horizontal |
| IDC20 | Connector_IDC / IDC-Header_2x10_P2.54mm_Vertical |
| Socket20 | Connector_PinSocket_2.54mm / PinSocket_2x10_P2.54mm_Vertical |
| SYNC | Connector_PinHeader_2.54mm / PinHeader_1x02_P2.54mm_Vertical |
| HDMI_Kycon_THT | Connector_Video / HDMI_A_Kycon_KDMIX-SL1-NS-WS-B15_VerticalRightAngle |
| VGA_DE15 | Connector_Dsub / DSUB-15-HD_Socket_Horizontal_P2.29x1.90mm_EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm |

VGA connector silkscreen endpoints are shortened to clear the board edge. Pad and
body geometry remain those of the source footprints. The connector source
files include links to the component drawings. Upstream library:
[KiCad footprints](https://gitlab.com/kicad/libraries/kicad-footprints).

`PTC_MF_R050` and `PTC_MF_R010` are independently drawn from Bourns MF-R
dimensions: 5.1 mm pitch, maximum widths 7.9 / 7.4 mm, 3.1 mm thickness,
0.9 mm holes and 1.8 mm lands. All component footprints in PCB-P2-THT are
through-hole, with the intentional exception of planar card-edge contacts.
Old PCB-P1 SMD footprint copies have been removed.

`AppleII_Edge50` and `WeAct_RP2350B_V1` are project-generated physical footprints,
using measurements documented in [PCB-FABRICATION.md](../PCB-FABRICATION.md).
M1's pads retain schematic names H1.n/H2.n. Connector shell pads retain SH,
including repeated SH pads where the shell has multiple contacts.
