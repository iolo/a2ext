# Upstream attribution

The `ref/` repositories remain unmodified by the implementation. Adapted source
is copied under `fw/` so builds do not depend on local changes in a reference
checkout. Exact upstream revisions are in `fw/dependencies.json`.

| Source | Adapted material | Preserved notices |
|---|---|---|
| Oliver Schmidt, a2pico | Demo 6502 ROM/linker layout and slot-terminal concept | MIT headers in demo source; `ref/a2pico/LICENSE` |
| Mark Aikens / David Kuder, AppleII-VGA via rallepalaveev | VGA renderers, RGB tables, fonts, PIO and scanline DMA | `fw/a2ext-vga/LICENSE` |
| Mark Aikens / David Kuder / Thorsten Brehm, A2DVI-Firmware | DVI renderers, fonts, TMDS patterns and library variant | `fw/a2ext-dvi/LICENSE` and source headers |
| Luke Wren / libdvi contributors | TMDS PIO serializer, DMA/queue and timing machinery, as bundled with A2DVI | `fw/a2ext-dvi/libdvi/LICENSE` |
| WeAct Studio | RP2350B Core Board V1.0 schematic, pinout and mechanical references | Vendor files under `ref/WeActStudio.RP2350BCoreBoard` |
| Raspberry Pi | Pico SDK/picotool build and peripheral APIs | External dependencies retain their own notices |

New integration includes the shared GPIO contract, carrier isolation and power
schematics, passive DMA capture, tagged experimental responses, shadow model,
frame adapters and verification tools. Port modifications are described in each
firmware README. No claim of upstream hardware endorsement or certification is
made. The original license texts travel with the adapted sources.
