# a2ext progress

Follow [PLAN.md](PLAN.md). Update this file and commit after every numbered step.
Only mark a step complete when its stated checks pass. Separate documentary,
automated, and physical validation.

## Status

- Steps 1-4 complete (documentary/automated checks); steps 5-21 pending.
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
