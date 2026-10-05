# Power tree simulation

LTspice model of the glasses' power path: battery → TPS63060 buck-boost → +3V3 → ME6211 LDOs (2.8 V and 1.5 V camera rails). Open `power_tree.asc` in LTspice; model files are in `models/`.

## Results

| Test | Condition | Typical loads | +25% camera loads | Limit | Pass? |
|---|---|---|---|---|---|
| Startup overshoot (VOUT peak) | VIN = 3.7 V | 3.552 V | 3.551 V | < 3.6 V (ESP32-S3 max) | ✅ (48 mV margin) |
| VOUT steady state | Before burst | 3.278 V | 3.278 V | 3.28 V nominal | ✅ |
| Load-step droop (VOUT) | 100 → 350 mA burst, 2 µs edges | 38.0 mV | 39.9 mV | — | — |
| CAM_2V8 LDO headroom | VOUT min − 2.8 V during burst | 0.44 V | 0.44 V | > LDO dropout (~0.1 V) | ✅ |
| VIN sag | During burst, 0.2 Ω battery resistance | 112 mV | 118 mV | — | — |

## Findings

- Startup overshoot reaches 3.55 V, 48 mV below the ESP32-S3's 3.6 V maximum. Thin margin; investigated further in the C1 and ESR sweeps.
- Droop is dominated by the ESP32 TX burst. A 25% heavier camera load changes it by under 2 mV, so results are not sensitive to camera current uncertainty.

## Assumptions

- **TPS63060:** TI unencrypted PSpice transient model (SLVM477A)
- **ME6211 LDOs:** behavioral model (no vendor model available); regulates ideally, so it shows dropout headroom but not real LDO transient ripple. Dropout approximated as 1 Ω
- **Camera loads:** OV3660 DS v1.3, table 8-3, external DVDD / 2.8 V I/O, typical (34 mA on 2.8 V, 64 mA on 1.5 V); +25% for margin. Full-resolution figures, so conservative for streaming at 720p or below
- **ESP32 load:** placeholder PWL (100 mA baseline, 350 mA TX burst); to be replaced by the measured profile from #2
- **Battery:** ideal source + 0.2 Ω placeholder internal resistance; to be replaced with the LP451165 datasheet value