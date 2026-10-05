# Power tree simulation

LTspice model of the glasses' power path: battery → TPS63060 buck-boost → +3V3 → ME6211 LDOs (2.8 V and 1.5 V camera rails). Open `power_tree.asc` in LTspice; models are in `models/`.

## Summary of findings

- **Startup overshoot is at the limit at full battery.** With all +3V3 capacitance modeled and sourced DC-bias derating, the startup peak at 4.2 V input is ~3.60 V (typical parts) and ~3.62 V for ~9 µs (worst-case ±20% tolerance). The ESP32-S3's 3.6 V supply limit is its absolute maximum (datasheet table 6-1).
- **Decision: V1 ships as designed.** Overshoot will be measured at V1 bring-up (#4); if over the limit, V1 boards can be reworked by hand. V2 fix tracked in #20.
- **C1 placement is correct.** The 10 pF capacitor from FB to GND matches the TPS63060 datasheet (§9.2.2.4) for power-save mode. Do not move it.
- **Load-step response is healthy.** ~40 mV droop under a 250 mA TX burst at nominal conditions; worst-case VOUT minimum 3.20 V (VIN 3.3 V), above the ESP32-S3's 3.0 V minimum.
- **No dropout on any rail** across the 3.0–4.2 V battery range; minimum CAM_2V8 LDO headroom 0.40 V.
- **Results are insensitive** to camera load (±25%) and capacitor ESR (2–30 mΩ).

## Startup overshoot (corrected model)

VIN = 4.2 V, C1 as built, all +3V3 capacitance (~107 µF nominal), 50 mA startup load, ESR 5 mΩ.

| Effective capacitance | Represents | Startup peak | Time above 3.6 V |
|---|---|---|---|
| 100% (~107 µF) | No derating | 3.532 V | none |
| 50% (~54 µF) | Typical parts (COUT: -45% at 3.3 V) | 3.601 V | ~1 µs |
| 42% (~45 µF) | Typical derating × -20% tolerance | 3.620 V | ~9 µs |

## Sensitivity studies (earlier model: COUT only, ~66 µF nominal, no startup load)

These runs omitted ~41 µF of +3V3 capacitance, so their absolute overshoot values are overstated. They remain valid for *trends* and for load-step behavior.

### Battery voltage

| VIN | Startup peak | Idle VOUT | Burst min | VIN during burst |
|---|---|---|---|---|
| 3.0 V | 3.464 V | 3.348 V | 3.222 V | 2.860 V |
| 3.3 V | 3.526 V | 3.349 V | 3.202 V | 3.145 V |
| 3.7 V | 3.552 V | 3.278 V | 3.240 V | 3.588 V |
| 4.2 V | 3.560 V | 3.278 V | 3.236 V | 4.101 V |

- Battery voltage has a small effect on overshoot (+8 mV from 3.7 → 4.2 V); capacitance derating dominates
- Below ~3.3 V input, the converter idles ~70 mV higher in power-save mode (PS/SYNC tied low)

### Output capacitance (VIN 3.7 V)

| Effective C per COUT cap | Startup peak | Burst droop |
|---|---|---|
| 10 µF | 3.596 V | 50.6 mV |
| 15 µF | 3.591 V | 44.2 mV |
| 22 µF | 3.560 V | 38.5 mV |

### ESR (VIN 3.7 V, C1 as built)

| ESR per cap | Startup peak | Burst droop |
|---|---|---|
| 2 mΩ | 3.583 V | 41.4 mV |
| 10 mΩ | 3.581 V | 42.2 mV |
| 30 mΩ | 3.575 V | 44.2 mV |

- Droop increase (+2.8 mV) matches the hand estimate ΔI × ESR/3 ≈ 2.3 mV

### C1 placement

Moving C1 to a feedforward position (VOUT → FB) reduced simulated overshoot but raised idle VOUT to ~3.34 V in power-save mode, the light-load behavior TI's recommended placement prevents. As-built placement retained.

## Assumptions and limitations

- **TPS63060:** TI unencrypted PSpice transient model (SLVM477A)
- **ME6211 LDOs:** behavioral model (no vendor model); shows dropout headroom, not real LDO transient ripple
- **Camera loads:** OV3660 DS v1.3 table 8-3, external DVDD / 2.8 V I/O, typical (34 mA on 2.8 V, 64 mA on 1.5 V); full-resolution figures, conservative for ≤720p streaming
- **ESP32 load:** placeholder PWL (50 mA from 50 µs, 100 mA baseline, 350 mA TX burst); to be replaced by the measured profile from #2
- **Output cap derating:** COUT (Samsung CL21A226MOQNNNE) -45% at 3.3 V per SEMCO data for the successor part CL21A226MOQNNNE#. Other +3V3 caps use the same global factor (not individually sourced)
- **Battery:** ideal source + 0.2 Ω placeholder; to be replaced with the LP451165 datasheet value

## Model history

An earlier version modeled only the three COUT capacitors and placed no load on VOUT during startup. It reported overshoot up to 3.668 V and flagged C1's placement as the cause. Review against the TPS63060 datasheet showed C1 matches TI's recommendation, and adding the ~41 µF of missing rail capacitance reduced the overshoot to the values above.

## Open items

- Measure V1 startup overshoot at bring-up (#4)
- Recheck low-battery VIN sag against the cell's protection cutoff once real internal resistance is known
- ESP32-S3 requires a supply capable of ≥0.5 A (datasheet table 6-2); the audio amp is not modeled

## Reproducing results

The schematic is committed at baseline (`variant=1`, `vBat=3.7`, `derate=0.55`, `esr=5m`). Sweeps are commented `.step` lines: uncomment one at a time and remove the swept parameter from the `.param` line before running.