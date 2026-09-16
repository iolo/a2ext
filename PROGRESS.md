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
- Steps 11-21 pending.
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
