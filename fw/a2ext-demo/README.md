# Demo

Default builds passively count bus cycles. UART0 is 115200 8N1 on IDC pins
1/2 with 3.3 V levels. Send `?` for capture/overflow/callback-drop counters;
reset transitions are reported. No daughterboard or slot-7 SYNC is required.

`-DA2EXT_DEMO_ACTIVE=ON` builds the experimental a2pico-derived slot ROM and
register demo. Requires ca65/ld65; runs from SRAM at 252 MHz (above the RP2350
rating). Qualify carrier power and response timing before use. Read the
limitations in `../a2ext-lib/README.md`. No hardware operation is claimed.

The 4096-byte ROM contains seven slot pages and C800 code. After qualification,
`PR#n` enters the terminal demo in slot n. Register offset 0 transfers a byte;
offset 1 reports bit 6 RX-ready and bit 7 TX-ready. Writing offset 1 releases
IRQ/NMI. UART ESC asserts IRQ and Ctrl-N asserts NMI. The bounded inter-core
FIFOs can drop UART input when full; this is a demonstration, not a reliable
serial adapter. Reset releases IRQ/NMI and C800 ownership.

`firmware.S` and `firmware.cfg` derive from Oliver Schmidt's a2pico demo;
original MIT notices are preserved. The banner is adapted to a2ext.
