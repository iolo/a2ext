# a2ext-vga

KiCad 10 schematic and project-local symbols for a passive 9-bit VGA
daughterboard. J1 follows the common IDC20 pinout. J2 is a female DE-15HD;
its abstract SH pin represents the connector shell. Select the connector's
exact shell/mounting pad numbers when a PCB is designed.

GPIO35-43 are R0-R2, G0-G2, B0-B2. GPIO44/45 are HSYNC/VSYNC. UART, GPIO46/47,
power, and RUN are unused. Both IDC ground contacts connect to VGA grounds and
shell. DDC, ID, and pin 9 power are unconnected, as specified in the PRD.

Each color has 2 kohm, 1 kohm, and 500 ohm resistors for bits 0, 1, and 2.
Use 1% tolerance. With a 75 ohm monitor load and ideal 3.3 V GPIO outputs:

`Vout = 3.3 * (b0/2000 + b1/1000 + b2/500) / (1/75 + 1/2000 + 1/1000 + 1/500)`

The eight nominal levels are 0, 0.0980, 0.1960, 0.2941, 0.3921, 0.4901,
0.5881, and 0.6861 V. Full-scale current is 9.15 mA per color; the MSB GPIO
supplies about 5.23 mA. Firmware pad drive settings must support this load;
start with 8 mA drive and verify voltage and edge quality on hardware. Real
GPIO output impedance changes these ideal values.

R10/R11 are 47 ohm series resistors on sync. Use direct mating to the carrier
for initial qualification; an IDC ribbon cable has no validated length.

Validation: KiCad ERC and exported named-net checks; physical levels and
640x480 timing are not yet tested. Run from the repository root:

```sh
python3 tools/schematics.py vga
python3 tools/check_schematics.py a2ext-vga
```

Design references: PRD resistor network and the bundled A2VGA2 schematic.
