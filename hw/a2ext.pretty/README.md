# a2ext physical footprint library

The KiCad 10 distribution footprint library provides the following local copies.
Copyright belongs to the KiCad library contributors. These redistributed
footprints and their modifications use CC-BY-SA 4.0 with KiCad's electronic-design
exception; the original [license document](LICENSE.md) is retained here.

| Local name | Original library / footprint |
|---|---|
| R0805 | Resistor_SMD / R_0805_2012Metric |
| R0402 | Resistor_SMD / R_0402_1005Metric |
| C0805 | Capacitor_SMD / C_0805_2012Metric |
| C1206 | Capacitor_SMD / C_1206_3216Metric |
| PTC1206 | Fuse / Fuse_1206_3216Metric |
| SS14 | Diode_SMD / D_SMA |
| IDC20 | Connector_IDC / IDC-Header_2x10_P2.54mm_Vertical |
| Socket20 | Connector_PinSocket_2.54mm / PinSocket_2x10_P2.54mm_Vertical |
| SYNC | Connector_PinHeader_2.54mm / PinHeader_1x02_P2.54mm_Vertical |
| HDMI_Molex | Connector_Video / HDMI_A_Molex_208658-1001_Horizontal |
| VGA_DE15 | Connector_Dsub / DSUB-15-HD_Socket_Horizontal_P2.29x1.90mm_EdgePinOffset3.03mm_Housed_MountingHolesOffset4.94mm |

Connector silkscreen endpoints are shortened to clear the board edge. Pad and
body geometry remain those of the source footprints. The connector source
files include links to the component drawings. Upstream library:
[KiCad footprints](https://gitlab.com/kicad/libraries/kicad-footprints).

`AppleII_Edge50` and `WeAct_RP2350B_V1` are project-generated physical footprints,
using measurements documented in [PCB-FABRICATION.md](../PCB-FABRICATION.md).
M1's pads retain schematic names H1.n/H2.n. Connector shell pads retain SH,
including repeated SH pads where the shell has multiple contacts.
