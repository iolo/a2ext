# Remaining work

Reviewed 2026-09-17 at commit `b24fc41`.

The project is a software-verified schematic and firmware prototype. All seven
planned deliverables exist: carrier/VGA/DVI schematics, the shared library, and
demo/VGA/DVI firmware. Hardware acceptance remains open.

Work through the checklist in order. Mark an item complete only when its
acceptance criteria have been met and supporting evidence recorded. Keep
software verification separate from physical qualification.

## Verified baseline

The following command passed during this review:

```sh
python3 tools/smoke.py --erc --firmware-from build/resumed
```

- Capture, slot-response logic, shadow-memory, and concurrent-load tests passed.
- VGA/DVI renderer replay passed for IIe and II/II+.
- All three schematic ERC/connectivity checks passed with zero violations.
- Three clean build configurations × three firmware targets passed, including
  ELF/UF2/map artifact and SRAM checks.

All 12 physical checks in [the measurement worksheet](docs/hardware-results.csv)
remain `NOT_RUN`. PCB layout and fabrication outputs are outside the current
scope.

## Completed design revisions

- [x] Remove CB3T switches and related supervisors, BUS_GOOD/OE control, and
  local support components. Carrier revision 0.2 uses direct bus connections;
  update its schematic/PDF/BOM, checks, and operating documentation.

- [x] Use slot-only power: retain F1/D1 to module H1.2 (5V/VSYS), remove D2,
  leave VBUS unconnected, and keep on-module U2 removed. Update flashing to
  external fixture power with USB data only (carrier revision 0.3).

- [x] Improve carrier wire labels: Apple II signals, UART functions, and
  IDC pin/GPIO names, with readable placement and unchanged connectivity
  (carrier revision 0.4).

- [x] Enlarge text and reflow all three schematics onto A4 landscape pages
  (carrier 0.5, VGA/DVI 0.2), preserving electrical connectivity.

## Ordered checklist

- [ ] **1. Prepare hardware and a measurement fixture.** Assemble prototypes,
  verify the required module modifications, identify the module regulator and
  RP2350 silicon revision, and obtain the measurement equipment. Record hardware
  revisions and assembly evidence. See the
  [carrier assembly notes](hw/a2ext-carrier/README.md) and
  [bench procedure](docs/HARDWARE-VALIDATION.md).

- [ ] **2. Validate direct-bus power behavior.** Measure slot startup/shutdown,
  brownouts, USB power disconnection, back-power, current, and temperature. Complete
  the [power-validation matrix](hw/a2ext-carrier/POWER-VALIDATION.md) and resolve
  failures before host connection. Record `PWR-01` and `PWR-02` results.

- [ ] **3. Validate passive capture.** Measure bus loading and setup/hold margins.
  Pass at least 30 minutes of sustained capture, plus deliberately induced
  overflow and recovery tests. Record `BUS-01` and `BUS-02` results.

- [ ] **4. Qualify active responses.** Measure selected/unselected response
  deadlines, data release, and contention. Exercise late replies, reset, FIFO
  faults, and C800 ownership. Resolve the documented falling-edge/reset races
  if they violate host timing; address unacknowledged callback side effects
  where required. Record `ACT-01` and `ACT-02` results. See the
  [responder limitations](fw/a2ext-lib/README.md).

- [ ] **5. Validate live I/O and video modes.** Exercise UART, IRQ/NMI, reset,
  optional/missing SYNC, shadow acquisition, banking, redraw, and II/II+/IIe
  display modes. Record `IO-01`, `IO-02`, and `VID-01` results.

- [ ] **6. Qualify VGA and DVI output.** Measure VGA DAC levels and sync timing;
  investigate the sync-line TODO in `fw/a2ext-vga/vga.c` (`vga_prepare_frame`).
  Verify DVI signal and monitor compatibility, reconnect behavior, and
  experimental 252 MHz stability across the intended operating envelope.
  Use direct daughterboard mating as the baseline. Record `VGA-01` and `DVI-01`
  results; also qualify the active demo's experimental clock during its tests.

- [ ] **7. Run combined-load acceptance.** For each video backend, sustain
  capture, video, and diagnostics together for at least 30 minutes. Measure
  stack high-water marks and CPU/DMA service margins. Require no capture
  overflows or callback drops and no increasing DVI missed-scanline count after
  startup. Record `LOAD-01` results.

- [ ] **8. Update acceptance records and project status.** Record measurements,
  conditions, firmware identity, and evidence in
  [hardware-results.csv](docs/hardware-results.csv) as each test is performed.
  Keep [PROGRESS.md](PROGRESS.md), the verification record, and README in sync
  with actual outcomes, leaving any unmet gates explicitly open.

## Supporting records

- [Implementation plan](PLAN.md)
- [Progress record](PROGRESS.md)
- [Software verification and limitations](docs/VERIFICATION.md)
- [Physical validation procedure](docs/HARDWARE-VALIDATION.md)
- [Measurement worksheet](docs/hardware-results.csv)
- [Resource and timing budgets](docs/resources.md)
