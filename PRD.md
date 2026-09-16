# a2ext

GOAL: General purpose Apple II Extension Card using the WeAct Studio RP2350B Core Board and daughter boards.

- Adapt a2pico's general hardware concept to RP2350B.
- Snoop all address range(A0..A15) like AppleII-VGA and A2DVI.
- Utilize 48 GPIOs of RP2350B instead of complex multiplexing for insufficient GPIO of RP2040/RP2350.
- Delegate specific functions to daughter boards, with a 20pin IDC connector for daughter boards rather than a single monolithic design.

EXPECTED OUTPUT:

1. a2ext-carrier kicad schematic and docs in hw/a2ext-carrier
2. a2ext-vga kicad schematic and docs in hw/a2ext-vga
3. a2ext-dvi kicad schematic and docs in hw/a2ext-dvi
3. a2ext-lib common library for a2ext-carrier daughter boards firmwares
3. a2ext-vga firmware in fw/a2ext-vga
3. a2ext-dvi firmware in fw/a2ext-dvi

## a2ext-carrier

The carrier accepts the WeAct Studio RP2350B Core Board V1.0 documented in
`ref/WeActStudio.RP2350BCoreBoard/HDK/`. Use its two 2x15, 2.54 mm pitch
headers (60 contacts total), not Pico/Pico 2 headers. These expose GPIO0..47
alongside power, reference, enable, and RUN contacts. The module schematic
specifies a 41.4 mm x 41.1 mm board; use the supplied dimension drawing and
STEP model for header placement and USB/button access.

Initial compatibility: Apple II/II+ and IIe, including IIe auxiliary-memory
video modes. Deliver schematics, BOMs, documentation, and firmware; PCB layout
and fabrication files are outside this release.

```
Apple II Peripheral Slot <--(50pin Edge Connector)--> RP2350B <--(20pin IDC Connector)--> daughter board
```

1. snoops Apple II BUS signals with RP2350B PIO state machines
2. (optional) makes a shadow copy of RAM
3. provides a 20pin IDC connector for daughter boards.

RP2350B is 5V tolerant, so no 74LVC245 or similar level shifter is needed.

Required Apple II bus signals required by RP2350B:

- D0..D7 : read/write
- A0..A15 : read only
- RWB : read only (1 for CPU read, 0 for CPU write)
- /DEVSEL : read only (0 on CPU access $C0n0..$C0nF; n=slot+8=9..F for slots 1..7)
- /IOSEL : read only (0 on CPU access $Cn00..$CnFF; N=slot=1..7)
- /IOSTRB : read only (0 on CPU access $C800..$CFFF)
- /RES : read only
- /IRQ : write only
- /NMI : write only
- SYNC : read only, composite video sync (slot 7 pin 19; motherboard-dependent)

## wiring

### Apple II slot (50-pin edge connector) <-> WeAct RP2350B module (two 2x15 headers)

The slot symbol uses counter-clockwise numbering, with pin 1 at the upper
left: 1–25 run down the left side and 26–50 run back up the right side.
Opposing contacts are 1/50, 2/49, through 25/26, matching the
[slot reference](a2slot.png) rotated 180 degrees.

```text
 1 /IOSEL  ┌─────────┐  50 +12V
 2 A0      │         │  49 D0
 3 A1      │         │  48 D1
   ...     │         │     ...
24 /DMAOUT │         │  27 /DMAIN
25 +5V     └─────────┘  26 GND
```

* IMPORTANT: GPIO should be assigned carefully for PIO block.

- 1 /IOSEL --> GPIO **TBD**
- 2 A0 --> GPIO **TBD**
- 3 A1 --> GPIO **TBD**
- 4 A2 --> GPIO **TBD**
- 5 A3 --> GPIO **TBD**
- 6 A4 --> GPIO **TBD**
- 7 A5 --> GPIO **TBD**
- 8 A6 --> GPIO **TBD**
- 9 A7 --> GPIO **TBD**
- 10 A8 --> GPIO **TBD**
- 11 A9 --> GPIO **TBD**
- 12 A10 --> GPIO **TBD**
- 13 A11 --> GPIO **TBD**
- 14 A12 --> GPIO **TBD**
- 15 A13 --> GPIO **TBD**
- 16 A14 --> GPIO **TBD**
- 17 A15 --> GPIO **TBD**
- 18 RWB --> GPIO **TBD**
- 19 SYNC --> GPIO **TBD** (slot 7 only; motherboard-dependent)
- 20 /IOSTRB - GPIO **TBD**
- 21 /RDY - N/C
- 22 /DMA - N/C
- 23 /INTOUT - 28 /INTIN
- 24 /DMAOUT - 27 /DMAIN
- 25 +5V_SLOT --(diode **TBD**)--> VSYS
- 26 GND --- GND; 26 GND --(100n cap.)-- 25 +5V
- 27 /DMAIN - 24 /DMAOUT
- 28 /INTIN - 23 /INTOUT
- 29 /NMI <--(pullup **TBD**)-- GPIO **TBD**
- 30 /IRQ <--(pullup **TBD**)-- GPIO **TBD**
- 31 /RES <--(pullup **TBD**)-- GPIO **TBD**
- 32 /INH - N/C
- 33 -12V - N/C
- 34 -5V - N/C
- 35 COLORREF - N/C
- 36 7M - N/C
- 37 Q3 - N/C
- 38 PH1 - N/C
- 39 USER1 - N/C
- 40 PHI0 --> GPIO **TBD**
- 41 /DEVSEL --> GPIO **TBD**
- 42 D7 <--> GPIO **TBD**
- 43 D6 <--> GPIO **TBD**
- 44 D5 <--> GPIO **TBD**
- 45 D4 <--> GPIO **TBD**
- 46 D3 <--> GPIO **TBD**
- 47 D2 <--> GPIO **TBD**
- 48 D1 <--> GPIO **TBD**
- 49 D0 <--> GPIO **TBD**
- 50 +12V - N/C

### 20pin IDC Connector <-> RP2350B

The 2x10 IDC header uses odd/even numbering: pins 1 and 2 are opposite
each other, followed by 3 and 4, through 19 and 20. TX/RX are on pins 1/2, VCC/GND are on pins 19/20.

```
   +-------+
TX | 1   2 | RX
   | 3   4 |
   | 5   6 |
   ...
5V | 19 20 | GND
   +-------+
```

- 1 TX <--> GPIO 0
- 2 TX <--> GPIO 1
- **TBD** Gn <--> GPIO n ; up to 14 free GPIOs for daughterboard
- **TBD** 3.3V <--(diode **TBD**)-- 3V3
- **TBD** /RESET --(pullup **TBD**--> RUN
- 19 5V <--(diode **TBD**)-- VSYS
- 20 GND --- GND

## a2ext-vga

a2ext-carrier daughterboard for VGA video output.

- used with a2ext-vga firmware.
- based on [A2VGA2 by rallepalaveev](https://github.com/rallepalaveev/AppleII-VGA/tree/main/A2VGA2),
  which is based on [AppleII-VGA](https://github.com/markadev/AppleII-VGA)

1. Read red, green, blue bits from a2ext-carrier IDC20 connector.
2. Convert to analog RGB using 3-bit weighted resistor DACs.
3. Output VGA signals through a female VGA connector.


### VGA (DE-15HD female) <--> a2ext-carrier 20pin IDC Connector

- 1 R <--(500 Ohm resistor, red bit 2)-- **TBD** R2
- 1 R <--(1K Ohm resistor, red bit 1)-- **TBD** R1
- 1 R <--(2K Ohm resistor, red bit 0)-- **TBD** R0
- 2 G <--(500 Ohm resistor, green bit 2)-- **TBD** G2
- 2 G <--(1K Ohm resistor, green bit 1)-- **TBD** G1
- 2 G <--(2K Ohm resistor, green bit 0)-- **TBD** G0
- 3 B <--(500 Ohm resistor, blue bit 2)-- **TBD** B2
- 3 B <--(1K Ohm resistor, blue bit 1)-- **TBD** B1
- 3 B <--(2K Ohm resistor, blue bit 0)-- **TBD** B0
- 4 N/C
- 5 GND -- 20 GND
- 6 GND -- 20 GND
- 7 GND -- 20 GND
- 8 GND -- 20 GND
- 9 N/C
- 10 GND - 20 GND
- 11 N/C
- 12 N/C
- 13 HSYNC <--(47 Ohm resistor)- **TBD** HSYNC
- 14 VSYNC <--(47 Ohm resistor)- **TBD** VSYNC
- 15 N/C
- Connector shell -- 20 GND

## a2ext-dvi

a2ext-carrier daughterboard for DVI video over an HDMI Type A connector.

- used with a2ext-dvi firmware.
- based on [A2DVI v5.x](https://github.com/rallepalaveev/a2dvi/tree/main/v5.x).

1. Read TDMS bit stream(encoded by a2ext-dvi firmware) from a2ext-carrier IDC20 connector.
2. Write to HDMI Type A connector.

### HDMI-SWM-19 <--> a2ext-carrier 20pin IDC Connector

- 1 D2+ --(270 Ohm resistor)-- **TBD** D2P
- 2 GND -- 20 GND
- 3 D2- --(270 Ohm resistor)-- **TBD** D2_N
- 4 D1+ --(270 Ohm resistor)-- **TBD** D1_P
- 5 GND -- 20 GND
- 6 D1- --(270 Ohm resistor)-- **TBD** D1_N
- 7 D0+ --(270 Ohm resistor)-- **TBD** D0_P
- 8 GND -- 20 GND
- 9 D0- --(270 Ohm resistor)-- **TBD** D0_N
- 10 CLK+ -- (270 Ohm resistor)-- **TBD** CLK_P
- 11 GND -- 20 GND
- 12 CLK- --(270 Ohm resistor)-- **TBD** CLK_N
- 13 N/C
- 14 N/C
- 15 N/C
- 16 N/C
- 17 GND -- 20 GND
- 18 VSYS (diode?) - 19 5V
- 19 N/C
- Connector shell -- 20 GND

## a2ext-lib

common library for a2ext-carrier daughter boards firmwares

- based on [a2pico](https://github.com/oliverschmidt/a2pico).
- but full address range(A0..A15) is snooped,
- and 48 GPIOs of RP2350B can be used instead of complex multiplexing for insufficient GPIO of RP2040/RP2350.

### files

- a2ext.c
- a2ext.h
- a2ext.pio : PIO program for snooping Apple II bus signals.
- and convenient stuff from a2pico to build RP2350B firmwares.

### functions(apis)

- void a2ext_init()
- uint16_t a2ext_getaddr() : read A0..A15(GPIO **TBD**)
- uint8 a2ext_getdata() : read D0..D7(GPIO **TBD**)
- void a2ext_putdata(uint8_t data) : write D0..D7(GPIO **TBD**)
- void a2ext_irq(bool on) : on/off /IRQ(GPIO **TBD**)
- void a2ext_nmi(bool on) : on/off /NMI(GPIO **TBD**)
- void a2ext_on_reset(void(*reset_handler)(bool on)) : register reset_handler for /RES (GPIO **TBD**)
- void a2ext_on_sync(void(*sync_handler)(void), uint32_t counter) : register sync_handler for SYNC(GPIO **TBD**)
- void a2ext_send(uint8_t data) : write to TX(GPIO 0; IDC20 pin1) : write lowest 8bits of uint32_t data into TX(GPIO 0;
  IDC20 pin1)
- void a2ext_on_receive(void(*receive_handler)(uint32_t data)) : register receive_handler for RX(GPIO 1; IDC20 pin2)

## a2ext-vga firmware

firmware for a2ext-carrier with a2ext-vga daughter board

- based on [AppleII-VGA](https://github.com/markadev/AppleII-VGA),
- modified for a2ext-carrier.
- physical snooping of Apple II bus signals is done by a2ext-carrier with a2ext-lib.

1. Read shadowed video framebuffer and I/O space(Apple II soft-switches)
2. Update VGA framebuffer
3. Write pixels, HSYNC, VSYNC into IDC20 connector.

## a2ext-dvi firmware

firmware for a2ext-carrier with a2ext-dvi daughter board

- based on [A2DVI-Firmware](https://github.com/ThorstenBr/A2DVI-Firmware),
- modified for a2ext-carrier.
- physical snooping of Apple II bus signals is done by a2ext-carrier with a2ext-lib.

1. Read shadowed video framebuffer and I/O space(Apple II soft-switches)
2. Update VGA framebuffer
3. Write TMDS signals to IDC20 connector.

## a2ext-demo firmware

firmware for a2ext-carrier without daughter board

- based on [a2pico demo](https://github.com/oliverschmidt/a2pico/tree/main/demo),
- modified for a2ext-carrier.
- physical snooping of Apple II bus signals is done by a2ext-carrier with a2ext-lib.

## References

- [WeAct Studio RP2350B Core Board](ref/WeActStudio.RP2350BCoreBoard/README.md)
- [Module schematic](ref/WeActStudio.RP2350BCoreBoard/HDK/RP2350B_SCH.pdf)
- [Module dimensions](ref/WeActStudio.RP2350BCoreBoard/HDK/尺寸图.pdf)

- [AppleII-VGA](https://github.com/markadev/AppleII-VGA) original by markadev
- [AppleII-VGA-rallepalaveev](https://github.com/rallepalaveev/AppleII-VGA) for RP2350B by rallepalaveev
- [A2DVI](https://github.com/rallepalaveev/a2dvi)
- [A2DVI-Firmware](git@github.com:ThorstenBr/A2DVI-Firmware.git)
- [A2C_DVI_Prototype](https://github.com/FarLeftLane/A2C_DVI_Prototype)
- [a2pico](https://github.com/oliverschmidt/a2pico)
- [Raspberry Pi Pico C SDK](https://www.raspberrypi.com/documentation/pico-sdk/)
