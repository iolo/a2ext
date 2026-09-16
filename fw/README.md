# Firmware development

Targets: `a2ext-demo`, `a2ext-vga`, and `a2ext-dvi`, with common code in
`a2ext-lib`. **At build-setup stage these are passive bring-up binaries, not
functional slot/video firmware.** Consult PROGRESS.md for implemented features.

Use Pico SDK 2.2.0, CMake >=3.20, GNU Make (or Ninja), and ARM GCC with newlib.
Pin references are in `dependencies.json`. Pico SDK needs its matching
picotool 2.2.0 for UF2 generation; provide an installed package with
`-Dpicotool_DIR=...` or allow the SDK's normal dependency download. PIO assembly
uses the matching SDK tool. No build modifies the bundled reference trees.

```sh
cmake -S . -B build -DPICO_SDK_PATH=/path/to/pico-sdk \
  -DPICO_TOOLCHAIN_PATH=/path/to/arm-toolchain -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Build outputs include ELF, UF2, and linker maps. The board definition targets
RP2350B/ARM with 16 MiB flash and deliberately omits default LED/button/SPI/I2C
pins. Do not use the stock WeAct board defaults: they overlap Apple II signals.
UART0 belongs to the a2ext API; SDK UART/USB stdio are disabled.

Never flash test binaries into a carrier connected to a host until the
carrier's electrical qualification gate has passed. Build validation does not
establish bus timing or successful video output.
