# Power and isolation acceptance gate

Status: **OPEN — no physical qualification has been performed.** The schematic
includes isolation rather than relying on unconditional RP2350 5 V tolerance.
Do not infer electrical qualification from an ERC pass.

## Design review

- RP2350 fault-tolerant digital pads tolerate 5.5 V at nominal 3.3 V IOVDD,
  but only 3.63 V with IOVDD off. ADC pads have different limits. None of the
  Apple II signals reaches an ADC pad in this design.
- CB3T3245 I/Os support 5.5 V operation and powered-off isolation. Its output
  high level tracks its supply, unlike a CB3Q switch. OE is pulled up to its
  own supply, as required by TI during power transitions.
- Supervisor thresholds are nominally 3.07 V and 4.65 V. Both monitor outputs
  must release before Q1 enables the switches. Reset release delay is nominally
  20 ms with CT open; falling-rail response is not instantaneous.
- BUS_GOOD has a pull-down as well as its pull-up; below the supervisor's valid
  operating range, control behavior and switch isolation must be measured.
- CB3T operation below its 2.3 V operating minimum is not established merely
  by the powered-off (0 V) Ioff specification. Brownout ramps and sudden supply
  collapse are required tests, not assumptions.
- Verify the exact WeAct regulator and flash parts on the purchased revision.
  Their identity and load capability are missing from the vendor schematic.
- GPIO pull-down defaults and the installed RP2350 silicon revision can affect
  bus loading at enable. Firmware must configure bus pads early and keep
  active response disabled until initialized. Test bootloader/RUN states too.

## Measurement procedure

Start with a current-limited bench fixture, prepared module, and controlled
TTL-level signal source in place of an Apple II. Probe slot 5 V, module 3.3 V,
BUS_GOOD, BUS_OE_N, and representative bus pins on both sides of a switch.
Include a data pin, interrupt pin, PHI0, and SYNC. Compare voltage waveforms
against datasheet limits throughout each transition, not just at steady state.

| Scenario | Required observation |
|---|---|
| Slot power rises, USB absent | Isolation until both monitored rails are valid |
| USB rises, slot off | Module powers; all Apple II bus connections remain isolated |
| Slot rises with USB already on | Enable only after the slot monitor's release delay |
| USB removed with slot on | Module remains powered; no unintended bus drive or reset |
| Slot falls with USB on | Switches isolate; no sustained back-power into host rails |
| Both sources removed | Isolation maintained through the complete decay |
| Slow ramp and repeated brownout | No chatter/unsafe pad voltage; log monitor thresholds |
| Forced module 3.3 V collapse, host signals high | Isolation before pad limits are exceeded |
| RUN held low; BOOTSEL/USB loader active | Data/IRQ/NMI do not contend with the host |
| UART/IDC attached, carrier off | No unintended supply path through signal/power pins |

Measure slot and USB reverse current with either source absent, module and
daughterboard current, regulator temperature, and the diode/PTC voltage drops
at maximum intended load. Measure daughterboard +5 V at the HDMI connector;
its valid range must be checked independently from module input voltage.

If any transition exceeds the pad limits or permits contention, revise the
control/hold-up circuit or isolation device and repeat the full matrix before
connecting to an Apple II. Component nominal behavior is not a substitute for
the worst-case timing review. Record module revision, silicon stepping, BOM,
temperature, supplies, scope settings, and waveform files with the results.

## Results

| Check | Status |
|---|---|
| Logical GPIO mapping and ADC exclusion | Automated check passed |
| Carrier ERC and named-net connectivity | Automated check passed |
| Manufacturer datasheet review | Performed; limitations above remain |
| All physical scenarios above | Not run — hardware/fixture unavailable |
| Regulator identity/current/thermal qualification | Not established |
| Release for host connection | Not approved by evidence yet |

References: [RP2350 electrical specifications](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf),
[SN74CB3T3245](https://www.ti.com/lit/ds/symlink/sn74cb3t3245.pdf),
[TPS3808](https://www.ti.com/lit/ds/symlink/tps3808.pdf).
