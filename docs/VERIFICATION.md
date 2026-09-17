# Verification record

Software verification on 2026-09-17; no assembled hardware or flashing was
available. A pass here does not close the physical acceptance gate.

Run from the repository root:

```sh
python3 tools/smoke.py
python3 tools/smoke.py --erc --firmware-from build/resumed
```

The first command needs Python 3, a C11 host compiler and pthreads. The second
also needs KiCad CLI and an existing configured Pico SDK build. It reads that
build's dependency paths, creates fresh build directories, and builds three
configurations: default IIe/passive demo, II/II+ with active demo, and video test
patterns. It checks all nine ELF/UF2/map sets and SRAM budgets. Build logs are
under `build/verify-*`; `build/last-verification.json` identifies the last matrix.
It does not flash or alter reference submodules.

| Check | Result | What it establishes |
|---|---|---|
| GPIO/IDC allocation | PASS | All 48 GPIOs allocated without collisions; video pairs and high-pin restrictions |
| KiCad ERC/netlists | PASS | Zero ERC violations; carrier 94, VGA 17, DVI 18 named nets checked |
| Clean firmware matrix | PASS | Three variants × three targets compile/link with warnings treated as errors |
| Passive capture logic | PASS | All 65,536 addresses, data/select/reset decoding, ordered block consumption, wrap and overwrite detection |
| Slot policy | PASS | Selection/address restrictions, C800 acquisition, other-slot release and CFFF release |
| Responder PIO logic | PASS | Actual 27-instruction source executes in a limited host interpreter; stale/zero tags, phase sweep, wrap and bounded release |
| Shadow traces | PASS | II/II+ and IIe bank precedence, IOUDIS/AN3, soft switches, initial unknown state, reset retention and loss invalidation |
| Concurrent shadow stress | PASS | 1,572,864 decoded writes while a desktop thread copies frames, including reset and epoch loss |
| Actual renderer replay | PASS | VGA token expansion and DVI TMDS decoding, output bounds, 640x480 frames, text/modes/page selection |
| Cross-backend text | PASS | Binary glyph positions match for normal/inverse/flashing text in both flash phases, 80 columns and alternate charset |
| Mixed/extended modes | PASS | Mixed text rows match text rendering; double modes produce distinct output; 80STORE suppresses page 2 |
| Physical capture/DMA timing | NOT RUN | Requires host or calibrated fixture and logic analyzer |
| Active slot timing/contention | NOT RUN | Requires qualified carrier, fixture and scope |
| Missing SYNC/live UART/reset/IRQ/NMI | NOT RUN | Hardware event behavior still needs measurement |
| Live capture plus VGA/DVI | NOT RUN | Desktop concurrency cannot establish RP2350 throughput or clock stability |
| Power sequencing/monitor compatibility | NOT RUN | See hardware validation procedure |

Renderer replay compiles the production renderer files with small host SDK and
output-sink substitutes. Undefined-behavior/bounds sanitizers are enabled; a
violation fails the run. Images are written to `build/replay/{IIE,IIPLUS}/`
as PPM files. Palette/artifact-color differences inherited from the two upstream
projects are allowed; text geometry and page-selection checks are exact.
There is no emulation of PIO synchronization, DMA arbitration or analog video.

Replay exposed and fixed unsigned-shift requirements in DVI double-hires and
II/II+ character-ROM flash semantics. Manual review added IIe IOUDIS gating for
AN3/DHIRES (Apple IIe Technical Reference Manual, table 2-10, p.29). Reset remains
conservative: RAM is retained and switches are reacquired from observed accesses.
A host redraw alone is insufficient if bank switches are still unknown; see the
explicit initialization sequence in the hardware validation guide.

Toolchain used: Pico SDK/picotool 2.2.0, ARM GCC 14.2.1, extracted newlib,
CMake Release configuration, ca65/ld65 for active-demo ROM, KiCad CLI 10.0.6.
Sources/revisions are in `fw/dependencies.json`. No PCB routing or fabrication
checks are included in this schematic-only release.
