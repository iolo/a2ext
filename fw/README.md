# Firmware build and flashing

Three targets share `a2ext-lib`: passive/optional active demo, VGA, and DVI.
These are software-checked prototypes; see [verification](../docs/VERIFICATION.md)
and the open [physical gate](../docs/HARDWARE-VALIDATION.md).

## Dependencies

- Pico SDK **2.2.0**, commit `a1438dff1d38bd9c65dbd693f0e5db4b9ae91779`.
- picotool 2.2.0 for UF2 generation, revision in `dependencies.json`.
- CMake >=3.20, Make or Ninja, ARM GCC/newlib. Validation used GCC 14.2.1.
- ca65/ld65 for `A2EXT_DEMO_ACTIVE=ON`; Python 3 for ROM embedding and checks.
- Host C11 compiler/pthreads for tests; KiCad CLI 10 for schematic checks.

The CMake build rejects a different Pico SDK version. Use the exact dependency
commits in [dependencies.json](dependencies.json) for reproduction. PIO assembly
uses the matching SDK tool. Supply an installed picotool CMake package via
`-Dpicotool_DIR=/path/to/picotool`; otherwise the SDK may download/build its
matching tool. USB stdio is disabled, and UART0 belongs to the a2ext library.
The firmware ports are self-contained and do not build source from `ref/`.

```sh
cmake -S . -B build/local -DPICO_SDK_PATH=/path/to/pico-sdk \
  -DPICO_TOOLCHAIN_PATH=/path/to/arm-toolchain \
  -Dpicotool_DIR=/path/to/picotool -DCMAKE_BUILD_TYPE=Release
cmake --build build/local -j4
```

Run at repository root. The toolchain directory contains `bin/arm-none-eabi-gcc`
and its newlib installation. If the compiler is already on PATH, the explicit
toolchain argument can be omitted. Choose a fresh build directory when changing
SDK/toolchain paths. Outputs are `a2ext-{demo,vga,dvi}.elf`, `.uf2`, and `.elf.map`.

For this workspace's restored toolchain, the verified configuration is:

```sh
cmake -S . -B build/resumed -DPICO_SDK_PATH=/home/iolo/pico-sdk \
  -DPICO_TOOLCHAIN_PATH=/home/iolo/workspace/retro/a2ext/.cache/arm-toolchain/usr \
  -Dpicotool_DIR=/home/iolo/pico-sdk/picotool -DCMAKE_BUILD_TYPE=Release
cmake --build build/resumed -j4
```

## Configuration

| CMake option | Default | Meaning |
|---|---|---|
| `A2EXT_APPLE_MODEL` | `IIE` | `IIE` or `IIPLUS` (also original Apple II); selects banking/font behavior |
| `A2EXT_DEMO_ACTIVE` | `OFF` | Compile 6502 ROM and enable experimental active slot responses; 252 MHz, SRAM execution |
| `A2EXT_VIDEO_TEST_PATTERN` | `OFF` | VGA test chart / DVI color bars while passive capture continues |

VGA/passive demo use 126 MHz. DVI uses 252 MHz to serialize 25.2 MHz pixels;
this exceeds the RP2350 rating and remains unqualified. Firmware does not alter
core voltage. Both video outputs default to 640x480/60 Hz with centered Apple
content. Models are selected explicitly, not auto-detected. See each target's
README for supported features and limitations.

The prepared-module board definition targets RP2350B/ARM and 16 MiB flash. It
omits stock LED/button/SPI/I2C defaults because those pins carry Apple II signals.
Do not substitute the stock WeAct definition. `tools/pinout.py` validates the
header generated from `hw/pinout.json`.

## Verification

```sh
python3 tools/smoke.py
python3 tools/smoke.py --erc --firmware-from build/local
python3 tools/memory_report.py build/local --size-tool /path/to/arm-none-eabi-size
```

The matrix uses fresh build directories and saves logs. It also exercises the
actual renderers on desktop traces, with PPM output under `build/replay`. Tests
never flash the module. UF2 generation is not evidence of hardware operation.

## Flashing procedure

No flashing has been performed in this project session. First complete module
preparation and the fixture power gate. Keep the Apple II disconnected during
bench flashing. A prepared module needs the carrier's replacement USB diode
path or an appropriate qualified fixture because on-module U2 was removed.

1. Hold BOOTSEL while applying USB power (or hold BOOTSEL and pulse module RUN).
2. Confirm the RP2350 boot drive appears; copy exactly one selected `.uf2` to it.
   Use the passive demo first, then a video test-pattern build on a fixture.
3. Let the module reboot; verify current draw and released host-bus pins before
   any host connection. UART uses IDC 1/2 at 3.3 V, 115200 8N1; no USB console.
4. After electrical qualification, perform the host/timing tests in the bench
   guide. Do not enable active mode merely because the passive image boots.

To recover an unsuitable firmware image, disconnect the host and repeat BOOTSEL
with a known passive image. Apple /RES does not reset the RP2350; module RUN does.
Archive the ELF, map, UF2 hash, options, dependency revisions and measurements
for each tested hardware configuration.
