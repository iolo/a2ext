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
4. a2ext-lib common library for a2ext-carrier daughter board firmware in fw/a2ext-lib
5. a2ext-vga firmware in fw/a2ext-vga
6. a2ext-dvi firmware in fw/a2ext-dvi
7. a2ext-demo firmware in fw/a2ext-demo

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

### Required WeAct module preparation

Use the V1.0 schematic as the reference and check the populated module revision
before changing components. With all power removed:

- Remove R16 (0 ohm) to disconnect GPIO23 from SW3 (KEY), its 5.1 kohm pull-up
  R18, and its associated protection/capacitor network. GPIO23 will carry D5.
- Remove R19 (5.1 kohm) to disconnect the U8 user LED from GPIO25. GPIO25 will
  carry D7. The separate power LED is unaffected.
- Leave U7 (secondary flash/PSRAM) and its optional R13/C23 unpopulated; remove
  R14 (0 ohm), if fitted, to isolate GPIO0 from the FLASH2_SS branch. UART TX
  must not toggle a secondary memory chip select or inherit its pull-up.
- Remove on-module U2 (the vendor's unidentified VBUS-to-5V power-path device).
  Carrier D1/D2 provide explicit slot/USB diode OR-ing through the module's
  exposed VBUS and 5V contacts. Do not confuse on-module U2 with carrier U2.
- Check for opens across the removed resistor pads and shorts to neighboring
  pads before installation. Pressing KEY must no longer connect GPIO23 to GND;
  GPIO25 must no longer connect to U8 through R19.

BOOTSEL, RUN/reset, primary flash, USB (with carrier D2), and SWD remain usable. The firmware must
not initialize GPIO25 as an LED or GPIO23 as a button. Never fit an unprepared
module: KEY could otherwise pull an Apple II data line low.

```
Apple II Peripheral Slot <--(50pin Edge Connector)--> RP2350B <--(20pin IDC Connector)--> daughter board
```

1. snoops Apple II BUS signals with RP2350B PIO state machines
2. (optional) makes a shadow copy of RAM
3. provides a 20pin IDC connector for daughter boards.

RP2350B digital fault-tolerant pads accept 5 V only with IOVDD powered to
3.3 V; ADC-capable pads do not share that rating. The carrier must include
power-off bus isolation where needed during startup/shutdown (approved design
refinement). Preserve full parallel address/data wiring; do not multiplex the
Apple II bus to save GPIOs. Electrical qualification is a release gate.

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
- PHI0 : read only, bus-cycle timing (slot pin 40)
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

* Pin assignments are defined in [hw/pinout.json](hw/pinout.json).
  Address/data/control inputs GPIO2..31 fit PIO GPIO base 0.
  All 33 Apple II bus connections use GPIO2..34; GPIO40..47 are reserved
  for the 3.3 V daughterboard interface, not 5 V Apple II signals.

- 1 /IOSEL --> GPIO 28
- 2 A0 --> GPIO 2
- 3 A1 --> GPIO 3
- 4 A2 --> GPIO 4
- 5 A3 --> GPIO 5
- 6 A4 --> GPIO 6
- 7 A5 --> GPIO 7
- 8 A6 --> GPIO 8
- 9 A7 --> GPIO 9
- 10 A8 --> GPIO 10
- 11 A9 --> GPIO 11
- 12 A10 --> GPIO 12
- 13 A11 --> GPIO 13
- 14 A12 --> GPIO 14
- 15 A13 --> GPIO 15
- 16 A14 --> GPIO 16
- 17 A15 --> GPIO 17
- 18 RWB --> GPIO 26
- 19 SYNC --> GPIO 34 (slot 7 only; motherboard-dependent)
- 20 /IOSTRB - GPIO 29
- 21 /RDY - N/C
- 22 /DMA - N/C
- 23 /INTOUT - 28 /INTIN
- 24 /DMAOUT - 27 /DMAIN
- 25 +5V_SLOT --(diode **TBD**)--> VSYS
- 26 GND --- GND; 26 GND --(100n cap.)-- 25 +5V
- 27 /DMAIN - 24 /DMAOUT
- 28 /INTIN - 23 /INTOUT
- 29 /NMI <--(pullup **TBD**)-- GPIO 33
- 30 /IRQ <--(pullup **TBD**)-- GPIO 32
- 31 /RES <--(pullup **TBD**)-- GPIO 31
- 32 /INH - N/C
- 33 -12V - N/C
- 34 -5V - N/C
- 35 COLORREF - N/C
- 36 7M - N/C
- 37 Q3 - N/C
- 38 PH1 - N/C
- 39 USER1 - N/C
- 40 PHI0 --> GPIO 30
- 41 /DEVSEL --> GPIO 27
- 42 D7 <--> GPIO 25
- 43 D6 <--> GPIO 24
- 44 D5 <--> GPIO 23
- 45 D4 <--> GPIO 22
- 46 D3 <--> GPIO 21
- 47 D2 <--> GPIO 20
- 48 D1 <--> GPIO 19
- 49 D0 <--> GPIO 18
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

The UART signals are named from the carrier's perspective (3.3 V logic).
Pin 18 resets the module through RUN and is separate from Apple II /RES.
Daughterboards may assert RUN low with an open-drain output; never drive it high.

| IDC pin | Carrier signal | GPIO |
|---|---|---|
| 1 | TX | 0 |
| 2 | RX | 1 |
| 3 | GPIO35 | 35 |
| 4 | GPIO36 | 36 |
| 5 | GPIO37 | 37 |
| 6 | GPIO38 | 38 |
| 7 | GPIO39 | 39 |
| 8 | GPIO40 | 40 |
| 9 | GPIO41 | 41 |
| 10 | GPIO42 | 42 |
| 11 | GPIO43 | 43 |
| 12 | GPIO44 | 44 |
| 13 | GPIO45 | 45 |
| 14 | GPIO46 | 46 |
| 15 | GPIO47 | 47 |
| 16 | GND | — |
| 17 | +3V3 output | — |
| 18 | RUN (active low) | — |
| 19 | protected +5V_DB output | — |
| 20 | GND | — |

There are 13 general-purpose daughterboard GPIOs in addition to TX/RX. GPIO46/47
are spare for VGA, and GPIO35/44..47 are spare for DVI. All daughterboard signal
pins use 3.3 V logic; in particular, GPIO40..47 are not 5 V-tolerant pads.
Use direct mating initially; ribbon-cable operation requires separate validation.

## a2ext-vga

a2ext-carrier daughterboard for VGA video output.

- used with a2ext-vga firmware.
- based on [A2VGA2 by rallepalaveev](https://github.com/rallepalaveev/AppleII-VGA/tree/main/A2VGA2),
  which is based on [AppleII-VGA](https://github.com/markadev/AppleII-VGA)

1. Read red, green, blue bits from a2ext-carrier IDC20 connector.
2. Convert to analog RGB using 3-bit weighted resistor DACs.
3. Output VGA signals through a female VGA connector.


### VGA (DE-15HD female) <--> a2ext-carrier 20pin IDC Connector

- 1 R <--(500 Ohm resistor, red bit 2)-- IDC 5 / GPIO37 R2
- 1 R <--(1K Ohm resistor, red bit 1)-- IDC 4 / GPIO36 R1
- 1 R <--(2K Ohm resistor, red bit 0)-- IDC 3 / GPIO35 R0
- 2 G <--(500 Ohm resistor, green bit 2)-- IDC 8 / GPIO40 G2
- 2 G <--(1K Ohm resistor, green bit 1)-- IDC 7 / GPIO39 G1
- 2 G <--(2K Ohm resistor, green bit 0)-- IDC 6 / GPIO38 G0
- 3 B <--(500 Ohm resistor, blue bit 2)-- IDC 11 / GPIO43 B2
- 3 B <--(1K Ohm resistor, blue bit 1)-- IDC 10 / GPIO42 B1
- 3 B <--(2K Ohm resistor, blue bit 0)-- IDC 9 / GPIO41 B0
- 4 N/C
- 5 GND -- 20 GND
- 6 GND -- 20 GND
- 7 GND -- 20 GND
- 8 GND -- 20 GND
- 9 N/C
- 10 GND - 20 GND
- 11 N/C
- 12 N/C
- 13 HSYNC <--(47 Ohm resistor)- IDC 12 / GPIO44 HSYNC
- 14 VSYNC <--(47 Ohm resistor)- IDC 13 / GPIO45 VSYNC
- 15 N/C
- Connector shell -- 20 GND

## a2ext-dvi

a2ext-carrier daughterboard for DVI video over an HDMI Type A connector.

- used with a2ext-dvi firmware.
- based on [A2DVI v5.x](https://github.com/rallepalaveev/a2dvi/tree/main/v5.x).

1. Read TMDS bit stream(encoded by a2ext-dvi firmware) from a2ext-carrier IDC20 connector.
2. Write to HDMI Type A connector.

### HDMI-SWM-19 <--> a2ext-carrier 20pin IDC Connector

- 1 D2+ --(270 Ohm resistor)-- IDC 8 / GPIO40 D2_P
- 2 GND -- 20 GND
- 3 D2- --(270 Ohm resistor)-- IDC 9 / GPIO41 D2_N
- 4 D1+ --(270 Ohm resistor)-- IDC 6 / GPIO38 D1_P
- 5 GND -- 20 GND
- 6 D1- --(270 Ohm resistor)-- IDC 7 / GPIO39 D1_N
- 7 D0+ --(270 Ohm resistor)-- IDC 4 / GPIO36 D0_P
- 8 GND -- 20 GND
- 9 D0- --(270 Ohm resistor)-- IDC 5 / GPIO37 D0_N
- 10 CLK+ -- (270 Ohm resistor)-- IDC 10 / GPIO42 CLK_P
- 11 GND -- 20 GND
- 12 CLK- --(270 Ohm resistor)-- IDC 11 / GPIO43 CLK_N
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
- uint16_t a2ext_getaddr() : read A0..A15(GPIO2..17)
- uint8_t a2ext_getdata() : read D0..D7(GPIO18..25)
- void a2ext_putdata(uint8_t data) : write D0..D7(GPIO18..25)
- void a2ext_irq(bool on) : on/off /IRQ(GPIO32)
- void a2ext_nmi(bool on) : on/off /NMI(GPIO33)
- void a2ext_on_reset(void(*reset_handler)(bool on)) : register reset_handler for /RES (GPIO31)
- void a2ext_on_sync(void(*sync_handler)(void), uint32_t counter) : register sync_handler for SYNC(GPIO34)
- void a2ext_send(uint8_t data) : transmit one byte on TX (GPIO 0; IDC20 pin 1)
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
2. Render the DVI output scanlines and encode TMDS data
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
