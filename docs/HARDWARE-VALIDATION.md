# Physical validation procedure

**Status: NOT RUN.** This repository contains schematic prototypes and firmware
that pass software checks. No assembled carrier, bus fixture or monitor was
available. Record results in `hardware-results.csv`; an empty measurement or
an ERC pass must not be treated as a physical pass.

## Equipment and record

Use a prepared WeAct V1.0 module, assembled carrier, directly mated daughterboard,
current-limited supplies, DMM, scope with low-capacitance probes, logic analyzer,
and a controlled 5 V bus fixture before connecting an Apple II. Include a 75-ohm
VGA termination and an appropriate differential probe for TMDS; do not load a
TMDS pair with a long single-ended probe ground lead. Record board/BOM revisions,
module regulator identity, RP2350 stepping, firmware commit and UF2 hash, host
model/slot, supply voltage, temperature, monitor/cable, instruments and waveform
paths. Photograph connector orientation and module modifications.

## 1. Assembly and power gate

With all power removed, verify module R16/R19/R14 and on-module U2 isolation,
secondary-memory population, slot orientation, ground continuity, chain links,
IDC pin 1, and open JP1 unless using a documented slot-7 SYNC source. Inspect
resistor values, switch variant (CB3T), supervisor parts and diode polarities.

Complete every scenario in
[POWER-VALIDATION.md](../hw/a2ext-carrier/POWER-VALIDATION.md), including both
source orders, source removal, slow ramps, rapid brownouts, RUN, BOOTSEL and
external UART power. Compare the entire voltage trace against component ratings;
identify the regulator and qualify current/temperature. Resolve failures before
connecting a host. Establish the maximum intended slot/daughterboard load and
check fuse/diode drop at that load. USB-only does not supply HDMI connector +5 V.

## 2. Passive capture and bus loading

Load the default passive demo with the host disconnected. Drive the fixture
through the qualified carrier with data outputs released. Replay sequential and
pseudorandom full addresses, walking data bits, reads/writes, selects, consecutive
cycles and reset transitions, first slowly and then at each host's actual bus
rate (include a 1.1 MHz stress point). Compare decoded cycles with the fixture
trace; use an instrumented capture dump or debugger only with the fixture halted.

Measure PHI0 and write-data setup/hold at both the slot and module pins. The PIO
sample is nominally about 254 ns after rising PHI0 at 126 MHz; include switch and
input-synchronizer delay in the measured margin. Compare against the installed
CPU's timing limits. Observe all signal rise/fall times and logic levels with
and without the carrier. Verify input pull behavior during startup and loader
entry. Read data is not guaranteed by this sampling instant and is not used to
populate shadow RAM.

Run at least 30 minutes of worst-case writes. Require zero unexplained lost,
duplicated or corrupted cycles and zero capture overflows. Deliberately delay
consumption using an instrumented firmware build: the overflow counter/epoch
must advance, stale queued data must be discarded, and shadow validity must be
cleared. Remove the delay and verify recovery after explicit switch setup and
RAM redraw. Save the instrumented source diff with results.

## 3. Active response, only after the preceding gates

Use `A2EXT_DEMO_ACTIVE=ON` on the fixture before a host. This build runs from SRAM
at experimental 252 MHz. Probe D0-D7, RWB, PHI0, /RES, all slot selects and switch
OE. Test every data bit in selected Cnxx ROM and C0n0 register reads/writes.
Confirm no output on RAM, writes, unselected cycles, or C800 without ownership.
Acquire ownership with local Cnxx, read C800, access another slot's Cnxx, and
verify release. Repeat with CFFF release and reset.

Measure request-to-valid data, setup at the CPU sampling edge, and release time.
Sweep response delays across rising/falling PHI0 in an instrumented build,
including an old response arriving during the following selected read/write.
Require no stale-cycle output and no contention with the fixture/host. The PIO
logic permits a final-enable race of up to four internal PIO cycles after a
falling edge, plus synchronization/propagation; acceptance depends on measured
host timing, not the host interpreter test. Reset can race an already queued
reply. If those cases violate host requirements, revise the responder or add
hardware gating before accepting active operation.

Induce FIFO loss: output must release and `slot_faulted` must latch. Confirm
explicit disable releases before stopping PIO. Never pause PIO/core debugging
on a live host bus. Callbacks are not acknowledged reads: UART/register side
effects can occur when a reply misses the CPU deadline. Qualify this behavior
before using the demo as anything beyond a terminal experiment.

## 4. UART, reset, interrupts and optional SYNC

With 3.3 V UART at 115200 8N1, exercise RX/TX bursts and `?` diagnostics while
capturing. Verify overflow/drop reporting. Check IRQ/NMI with a scope: assertion
is low, release is high impedance with host pull-ups, and Apple reset releases
both. The active demo maps UART ESC to IRQ and Ctrl-N to NMI; a write to register
offset 1 releases them. Verify correct host handling with a suitable IRQ/NMI
handler installed before asserting either.

Keep JP1 open and confirm both video targets operate without SYNC. On a verified
slot-7 source only, close JP1 and instrument a registered callback; confirm it
counts composite-sync falling edges with the requested divider, not PHI0. Check
counter 0/unregister and missing-input behavior. Check reset callback ordering
and data-pin release through repeated host resets and module RUN operations.

## 5. Shadow acquisition and video modes

Capture cannot reconstruct RAM written before startup or before an overflow.
Unknown-bank writes are discarded, and RESET retains RAM but reacquires switch
state from subsequent accesses. For a repeatable IIe bench test, at a normal
main-memory Applesoft prompt explicitly initialize switches, then redraw:

```basic
POKE 49152,0:POKE 49154,0:POKE 49156,0:POKE 49160,0
POKE 49164,0:POKE 49166,0:POKE 49278,0:POKE 49247,0
POKE 49236,0:POKE 49238,0:POKE 49234,0:TEXT:HOME
```

This is a diagnostic setup that changes display/banking state; do it between
applications, not inside a program relying on auxiliary memory. For II/II+ use
the IIPLUS build and `TEXT:HOME`. After loss/reset repeat setup and redraw. UART
`known` reports acquired flags; no firmware feature automatically reads host RAM.

Compare host and reproduced output for 40-column normal/inverse/flashing text,
lores, hires, mixed text rows, both pages, IIe 80-column/alternate charset,
double-lores/double-hires, AUXWRITE/ALTZP/80STORE interactions, and IOUDIS gating.
Use deliberately different main/aux patterns. Verify reset retains observed RAM
and loss never silently presents old shadow as fully valid. Unknown bytes are
rendered as zero and may produce visible placeholder glyphs.

## 6. VGA and DVI acceptance

Start with the test-pattern firmware, then host modes. VGA: measure each DAC bit
and full white into 75 ohms (ideal full scale 0.6861 V), monotonicity, channel
order and sync levels. Nominal output: 25.2 MHz pixels, 31.5 kHz lines, 60 Hz
frames, negative sync, 800x525 totals, 96-pixel HSYNC and 2-line VSYNC. Check
content placement, blanking, pulse widths and no visible underruns.

DVI: verify connector +5 V under load, pair polarity/levels and clock, stable
640x480 lock, absence of sparkles/dropouts, and reconnect/power-order behavior.
Use multiple monitors and record each cable. The 252 MHz clock exceeds RP2350's
150 MHz rating: verify repeated cold starts and sustained operation across the
intended supply/temperature envelope. No core-voltage override is authorized by
this design. Direct mating is the baseline; qualify each ribbon configuration
separately with signal-integrity measurements.

For each video backend, repeat the 30-minute capture stress with maximum-rate
host screen writes and UART diagnostics. Capture overflow/callback-drop counters
must remain unchanged; after startup, DVI `video_errors` must not increase.
Measure stack high-water marks and CPU/DMA margins using an instrumented build.
Log faults; a desktop replay or clean UF2 build cannot substitute for this test.
