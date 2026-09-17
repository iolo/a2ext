# a2ext progress

Follow [PLAN.md](PLAN.md). Update this file and commit after every numbered step.
Only mark a step complete when its stated checks pass. Separate documentary,
automated, and physical validation.

## Status

- Steps 1-5 complete (documentary/automated checks).
- Step 6 resource allocation and passive/video assembly checks complete;
  active-response implementation/timing proof deferred to step 14.
- Step 7 schematic draft complete; step 8 procedure/review complete, physical
  acceptance blocked on hardware and a measurement fixture.
- Steps 9-10 daughterboard schematics complete (automated checks).
- Steps 11-13 build setup, passive capture, and API definition complete (software checks).
- Step 14 implemented and software-checked; physical active-response timing open.
- Step 15 shared shadow model complete (host traces).
- Step 16 VGA port builds; replay/physical display acceptance pending.
- Step 17 DVI port builds; replay/physical display acceptance pending.
- Step 18 clocks, priorities and RAM budgets checked; runtime timing open.
- Step 19 automated software/ERC checks pass; physical coverage remains open.
- Steps 20-21 validation procedures, build/flashing docs and attribution complete.
- Software/design deliverables are committed; physical acceptance is still open.
- Hardware acceptance: not tested; no assembled hardware available in this session.

## Work log

### Planning baseline — 2026-09-17

- Saved the agreed 21-step implementation plan, including the per-step progress
  update and commit rule.
- Confirmed the WeAct reference module is present and KiCad CLI/CMake are
  installed. ARM GCC and Ninja are not on PATH; investigate before step 11.
- The user's staged `.gitmodules` and WeAct submodule addition predate this work;
  preserve those changes and exclude them from task commits unless requested.
- Validation: inspected repository status and local module reference paths.
- Blockers: none for starting documentation; hardware power sequencing and
  physical qualification remain explicit later gates.

### Step 1 — module and connector contract

- Updated PRD to target WeAct RP2350B Core Board V1.0, two 2x15 headers,
  60 contacts, and the module's 41.4 x 41.1 mm outline.
- Recorded II/II+/IIe compatibility and schematic-only hardware deliverables.
- Validation: compared the supplied schematic, pinout image, and dimension PDF;
  confirmed both headers number 1-30. No hardware measurements performed.
- Blockers: none for this step; physical module revision must match the reference.

### Step 2 — PRD corrections and complete deliverable list

- Corrected IDC RX, TMDS spelling, the data return type, UART description, and
  DVI rendering description. Numbered all seven outputs and included the demo.
- Validation: inspected the PRD diff; `git diff --check` passes.
- Blockers: none.

### Step 3 — WeAct module preparation

- Added powered-off preparation and continuity checks for R16 (KEY/D5), R19
  (LED/D7), and the optional secondary-memory branch on GPIO0.
- Also require R14 removal when fitted, avoiding the unused FLASH2_SS branch
  and its optional pull-up on UART TX. Keep U7/R13/C23 unpopulated.
- Validation: visually inspected the rendered vendor schematic, not only text
  extraction; R16/R19/R14 connections match the documented preparation.
- Physical module revision and resistor removal are not verified in this
  session; these are assembly prerequisites, not claimed physical work.

### Step 4 — GPIO contract

- Filled all Apple II GPIO assignments and added PHI0 to the required signals.
- Added `hw/pinout.json` as the pin-allocation source and a generated firmware
  header. `tools/pinout.py` checks uniqueness, slot/address/data ordering,
  PIO range, open-drain interrupt declarations, and exclusion of ADC pads
  from the 5 V bus.
- Validation: generator and subsequent read-only check pass; 33 bus + 2 UART +
  13 daughterboard GPIOs cover GPIO0-47 exactly; `git diff --check` passes.
- Blockers: electrical qualification remains pending; this is a logical map.

### Step 5 — daughterboard connector contract

- Assigned all IDC20 contacts, both video mappings, a second ground, 3.3 V,
  protected 5 V, and RUN. Distinguished module reset from Apple II reset.
- Extended the source pin map and generated header with VGA/DVI pins. Validate
  all 20 IDC contacts and adjacent TMDS pairs; the clock uses an even/odd pair
  to share a PWM slice with the reference serializer.
- Validation: regeneration, pin-contract check, and whitespace check pass.
- Blockers: protected power implementation and physical interface validation
  remain for hardware steps; no daughterboard has been tested.

### Step 6 — PIO, DMA, timing, and memory budgets

- Assigned separate PIO blocks and DMA IRQs; documented 126 MHz passive/VGA
  and experimental 252 MHz DVI clocking, buffer/memory budgets, and high-GPIO
  SDK requirements. Added the passive-capture PIO source.
- Validation: built pioasm from Pico SDK 2.2.0 in /tmp; assembled the capture
  program (3 words), bundled VGA programs (9+8+11 = 28 words), and bundled
  non-debug DVI serializer (2 words). Each fits its assigned PIO instruction
  store. Up to 8/16 DMA channels are reserved for capture plus DVI.
- Active response has a separate 32-word reservation but no assembled design
  or timing proof yet. Physical capture timing is also unverified. These
  limitations are explicit in `docs/resources.md`, not marked as test passes.
- User approved power-off bus isolation where required; updated PLAN/PRD.
- Blockers: none for daughterboard schematics; carrier isolation circuit still
  needs detailed electrical review in steps 7-8.

### Step 7 — carrier schematic draft

- Created a self-contained KiCad carrier project, local symbols, BOM, PDF,
  net contract, generator, and assembly/power documentation.
- Added five CB3T3245 bidirectional isolation/translation switches, dual rail
  supervisors, default-off OE control, separate RUN and Apple reset, optional
  slot-7 SYNC jumper, and explicit fused slot/USB power paths.
- Extended module preparation to remove the unidentified on-module U2 power
  path; carrier D2 restores USB power with a known diode connection.
- Validation: KiCad 10 ERC has zero violations; exported netlist verifies all
  48 module GPIO contacts, 33 switched bus paths, IDC pins, and chain links.
  Visually inspected the schematic PDF. No physical measurements performed.
- Blockers: module regulator rating, brownout timing, and host signal loading
  remain unqualified; this is a schematic prototype, not a fabrication release.

### Step 8 — power-sequencing gate

- Documented the isolation ratings, supervisor thresholds, undefined ramp
  regions, module-part uncertainties, and an explicit power-source/brownout
  measurement matrix in `hw/a2ext-carrier/POWER-VALIDATION.md`.
- Removed KiCad's per-user `.kicad_prl` state from tracking and added generated
  build/cache ignores.
- Validation: manufacturer datasheet review and the earlier ERC/net checks;
  no physical qualification is claimed.
- Blocker: no assembled carrier, identified module regulator, or scope fixture
  is available. Keep this gate open while independent steps continue.

### Step 9 — VGA daughterboard

- Added the VGA KiCad project, local symbols, BOM, PDF, and connectivity
  contract with 9 DAC resistors and two sync resistors.
- Documented nominal 75-ohm DAC levels (0-0.6861 V), per-pin loading, grounding,
  and the direct-mating baseline.
- Validation: zero ERC violations and exported netlist checks; ideal DAC
  calculation checked. Physical signal levels/timing remain untested.
- Blockers: physical acceptance requires a built board, scope, and monitor.

### Step 10 — DVI daughterboard

- Added the HDMI Type A schematic, project-local symbols, BOM, PDF, and
  connectivity contract; all four TMDS pairs use 270-ohm series resistors.
- Documented pair polarity, clock PWM pairing, GPIO-base/mask changes required
  by libdvi, fused pin-18 supply, unused interfaces, and direct mating.
- Validation: zero ERC violations and exported netlist checks; compared
  positive/negative mapping with the reference serializer instructions.
- Blockers: no physical TMDS/monitor tests; abstract connector shell pin must
  be mapped to the chosen part if PCB layout is later undertaken.

### Step 11 — reproducible firmware build setup

- Added CMake targets for demo/VGA/DVI, shared-library build rules, prepared
  WeAct board definition, dependency revisions, and build instructions.
- Initial targets only initialize bus pins as inputs; they do not yet capture,
  respond to slot reads, or generate video. Default LED/button pins are absent.
- Validation: built all three ELF/UF2/map sets using Pico SDK/picotool 2.2.0 and
  ARM GCC 14.2.1/newlib. Compiler packages were extracted under /tmp without
  changing system packages; build artifacts stay in ignored `build/`.
- The SDK warns that TinyUSB is absent; USB stdio is explicitly disabled and
  all targets built successfully. No physical flashing was performed.
- Blockers: none for software implementation; the hardware gate remains open.

### Step 12 — passive DMA bus capture

- Added chained DMA capture into two 1024-word blocks, atomic cycle decoding,
  FIFO-stall/overwrite detection, stream epochs, and resynchronization. Demo
  now consumes the passive capture stream; video targets remain bring-up code.
- Capturing, polling, stopping, and statistics access belong to the same core;
  its DMA IRQ1 owns completion handling. No UART/render callback runs there.
- Validation: all three targets rebuild successfully. Host tests cover every
  16-bit address, data/select decoding, ordered block consumption, repeated
  wrap, and rejection when DMA would overwrite an unread or partial block.
- On resume, /tmp dependencies were gone. Reused the matching SDK at
  `/home/iolo/pico-sdk`, restored ARM packages under ignored `.cache/`, and
  created `build/resumed`. The SDK now has TinyUSB, still disabled for stdio.
- Blockers: physical PIO sampling, DMA throughput, and electrical qualification
  remain untested; host queue tests do not emulate the RP2350 DMA engine.

### Step 13 — common library API

- Added latched address/data getters, open-drain IRQ/NMI helpers, UART0 byte
  transport, and deferred reset/receive/composite-SYNC callbacks. Reset releases
  interrupt outputs; callback queue overflow is observable.
- Documented core ownership, callback dispatch limits, SYNC counting, capture
  epochs, and read-data limitations. `try_putdata` still rejects all output
  until the bounded active response path is implemented in step 14.
- Validation: all three targets compile/link with warnings treated as errors;
  capture decoding/queue regression tests still pass. GPIO/UART behavior has
  not been tested on hardware.
- Blockers: active response implementation and physical timing proof remain.

### Step 14 — experimental slot responder and a2pico demo

- Added an opt-in 27-word PIO responder with per-cycle tags, C800 ownership,
  CFFF release, delayed write sampling, and fail-closed FIFO/mismatch faults.
  Ported the MIT a2pico 6502 ROM and UART/register/IRQ/NMI demo. Default remains
  passive; active builds explicitly use experimental 252 MHz and SRAM code.
- Validation: active and passive firmware builds, host slot-policy regression,
  and an instruction-level PIO test pass. The latter sweeps reply enqueue
  phases, rejects stale/zero tags, checks wrap, and checks bounded release;
  it does not model synchronizers, CPU latency, or electrical timing.
- Limitations: no physical response deadline proof. Final enable can race a
  falling edge (up to four PIO cycles to release, plus synchronization), reset
  does not cancel an already queued PIO reply, and callback side effects are
  not acknowledged by successful CPU sampling. Active mode is experimental.

### Step 15 — shared video shadow

- Added 64 KiB main/aux banks with byte validity, II/II+ versus IIe selection,
  video switches, ALTZP/AUXWRITE/80STORE precedence, and capture-epoch loss
  invalidation. Read cycles never populate RAM from unqualified read data.
- Extended passive samples to include /RES in the same 32-bit DMA word, so
  reset handling follows captured bus order rather than delayed callbacks.
  Warm reset retains RAM/validity and conservatively reacquires switches;
  writes with unknown bank selection are ignored until selection is known.
- Cross-core readers use atomic bytes and validity; frame copies may tear but
  avoid undefined concurrent accesses. I/O, ROM, language-card and expansion
  banking are explicitly outside the RAM shadow contract.
- Validation: host traces pass for bank precedence, 40/80-column and graphics
  switches, reset retention, unknown initial contents, and capture loss.
  Three firmware targets rebuild; capture and slot regressions pass.

### Step 16 — VGA renderer and output port

- Ported the bundled AppleII-VGA text/lores/hires/double-mode renderer, fonts,
  scanline DMA and 28-word PIO programs with MIT attribution. Shared capture
  begins on core 1 before renderer initialization; frame copies isolate the
  renderer from concurrent shadow writes. Added IIe/II+ and test-pattern builds.
- Corrected PIO1 GPIO base, nine-pin OUT setup and RGB bit order, including
  precomputed artifact-color tables. Output remains 640x480 with centered
  560x384 content; model-specific font selection is explicit.
- Validation: all firmware targets compile/link with -Werror. Host renderer
  replay is scheduled in step 19; physical sync/color/throughput checks remain
  open. Added 48 KiB frame-copy storage beyond the original memory estimate;
  final linker-size accounting is step 18 work.

### Step 17 — A2DVI renderer and serializer port

- Retained A2DVI's text/lores/hires/double-mode renderers, TMDS palettes and
  libdvi PIO/DMA serializer with licenses. Adapted high-pin masks, PIO1 base 16,
  RAM sections, pair polarity, model/font selection and shared frame copies.
- Removed upstream debug/status-row demand from the scanline consumer; it now
  displays 384 content lines centered in 480. Eight TMDS buffers use 30 KiB.
  No original transceiver capture, menus, LED/button GPIOs or custom flash
  configuration code runs in this target.
- Validation: all three firmware targets compile/link with -Werror. Renderer
  replay is step 19 work; hardware DVI/capture throughput is not measured.
  The required 252 MHz remains explicitly experimental with no voltage change.

### Step 18 — clock, priority and memory integration

- Fixed both outputs at nominal 640x480/60 Hz (25.2 MHz pixels, 800x525 total).
  Capture remains 126 MHz across VGA/DVI system clocks, with a dedicated core,
  high-priority DMA/IRQ and SRAM hot paths. UART diagnostics are bounded and
  nonblocking; DVI exposes missed-scanline count.
- Added ELF SRAM accounting including frame copies and a separate DVI runtime
  buffer/queue allowance. Current VGA total is 232,332 bytes; DVI conservative
  total is 288,060 bytes, within 520 KiB. No full RGB framebuffer is allocated.
- Validation: all three Release builds pass, clock/divider arithmetic reviewed,
  memory report passes. PLL/timing/overclock stability and simultaneous live
  capture/render throughput remain physical acceptance tests, not build claims.

### Step 19 — automated checks and renderer replay

- Added one-command host/pin/ERC verification and clean firmware matrices for
  IIe, II/II+ with active demo, and video patterns. All nine ELF/UF2/map sets
  build, and SRAM budgets pass. All three schematics retain zero ERC violations.
- Replayed real VGA/DVI renderer sources into host pixel sinks with bounds/UB
  sanitizers. Checked dimensions, page/80STORE selection, mixed text rows,
  double modes and matching normal/inverse/flashing/alternate text in both
  host models. Saved reproducible PPM artifacts under ignored build/replay.
- Fixed DVI double-hires signed shifts, II/II+ character-ROM flash handling and
  flash-phase agreement. Added IOUDIS gating after inspecting the Apple IIe
  Technical Reference Manual table 2-10. Retained conservative reset recovery.
- Concurrent desktop test passes 1,572,864 decoded writes with frame snapshots,
  reset and capture-loss invalidation. It does not benchmark target DMA.
- Detailed coverage/limitations are in docs/VERIFICATION.md. Physical missing
  SYNC, UART/interrupt behavior, response timing and live video/capture load
  tests cannot run without hardware; those acceptance items remain open.

### Step 20 — physical validation procedure

- Published fixture-first assembly/power, passive capture/loading, active timing,
  IRQ/NMI/reset/UART/SYNC, video levels/monitor stability and simultaneous-load
  procedures with measurable acceptance conditions and an evidence worksheet.
- Documented explicit IIe switch initialization/redraw for conservative shadow
  acquisition and the unresolved active-response edge/reset races.
- Validation: reviewed against implemented pin/resource/API contracts and the
  existing power gate. Every physical worksheet entry remains NOT_RUN; no board,
  instrument reading, flashing, monitor result or live host test is claimed.

### Step 21 — documentation and handoff

- Replaced the placeholder README with deliverable links, build/check workflow,
  compatibility matrix, module preparation, initialization behavior, attribution
  and explicit physical limits. Expanded firmware setup/options/flashing and
  recovery instructions; included the verified local toolchain configuration.
- Resolved obsolete PRD power/pull-up placeholders to match the schematics and
  updated the plan's power gate wording to the approved isolation design.
- Validation: reviewed local documentation links and repository diff; final
  source builds and software checks passed in step 19. No flashing performed.
- Remaining acceptance: step 8 power qualification, active response edge/reset
  races and setup/hold timing, target capture/render load, UART/interrupt/SYNC,
  VGA levels and DVI stability. The measurement worksheet records all as NOT_RUN.
  Completion of documentation does not close these physical gates.
