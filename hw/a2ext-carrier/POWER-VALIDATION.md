# Direct-bus power validation

Status: **OPEN — no physical qualification has been performed.** Carrier
revision 0.3 connects the Apple II bus directly to the module. The user approved
removing the CB3T switches and their supervisor/control circuit on 2026-09-17.
Revision 0.3 additionally removes USB power; slot input is the only supply.
This replaces the earlier isolation and dual-source procedures.

## Operating assumptions

- All operating power enters through slot pins 25/26. For off-host flashing,
  use a current-limited 5 V fixture at these pins and connect USB for data only.
  Do not hot-plug the card.
- RP2350 fault-tolerant digital inputs tolerate up to 5.5 V with IOVDD at
  3.3 V; their unpowered tolerance is only 3.63 V. GPIO2-34 carry the bus;
  ADC-capable GPIO40-47 are reserved for the daughterboard.
- There is no automatic bus disconnection during a module supply failure or
  RUN assertion. A live 5 V bus with the module unpowered is unsupported.
- Slot pin 25 feeds F1, then D1, then VSYS at module H1.2 (marked 5V).
  D1 retains reverse-current protection. Carrier D2 is removed, H1.1 (VBUS)
  is unconnected, and on-module U2 remains removed to disable USB power.
  The daughterboard +5V_DB is supplied through F1/F2 before D1.
- External UART/IDC devices must not drive an unpowered carrier or power it
  through signal pins. J2 supply pins are outputs.
- Verify the actual WeAct regulator, flash, and silicon revision. The vendor
  schematic does not identify the regulator or establish its load capability.

## Measurement procedure

Use a current-limited fixture before a host. Probe slot 5 V, VSYS (module 5V input),
module 3.3 V (IOVDD), and representative GPIOs: data, IRQ/NMI, PHI0, and SYNC.
Capture their relative voltage ramps and compare them against device limits
throughout transitions. Powering the regulator from the slot alone is not
proof of acceptable sequencing. Keep fixture outputs released until the
module is powered; characterize supply ramps before applying driven bus cycles.
Do not deliberately apply 5 V to an unpowered module to test for damage.

| Scenario | Required observation |
|---|---|
| Slot-powered startup, USB disconnected | Record relative slot, IOVDD, and GPIO ramps; establish input-voltage margins |
| Slot-powered shutdown | Record full decay; GPIO voltage remains within the applicable limits as IOVDD falls |
| Slow supply ramp and brownout | Establish the operating envelope and any interval outside the documented input conditions |
| RUN assertion/release with valid supplies | No unintended data/IRQ/NMI drive; pins remain physically connected |
| Fixture-powered BOOTSEL, card removed from host; USB data attached | Stable VSYS/3.3 V and boot-drive enumeration; fixture bus released |
| USB attached with fixture power absent, card removed from host | No powered module/HDMI rail; verify U2 removal and absence of D2 |
| Slot/fixture power present, USB disconnected | No supply feed into module VBUS/USB connector |
| UART/IDC attachment | No signal or supply back-power when either side is off |

Measure module/daughterboard current, regulator temperature, and diode/PTC
voltage drops at the intended load. Check HDMI +5 V independently of the module
input. Record board/module revision, silicon stepping, BOM, temperature,
supplies, probe settings, and waveform files with `PWR-01`/`PWR-02` results in
[the worksheet](../../docs/hardware-results.csv).

If normal transitions exceed ratings or show contention, record the failure
and revise the power arrangement before physical acceptance. Direct-bus
reference designs motivate this simpler circuit; they do not establish the
WeAct module's measured power behavior.

## Results

| Check | Status |
|---|---|
| Logical GPIO mapping and ADC exclusion | Automated check passed |
| All physical scenarios above | Not run — hardware/fixture unavailable |
| Regulator identity/current/thermal qualification | Not established |

Reference: [RP2350 electrical specifications, §12.2](https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf).
