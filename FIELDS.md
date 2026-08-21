# Fields

Decoded Modbus fields for the Anker SOLIX Solarbank 4 E5000 Pro.

Raw register values are decoded as the listed type, then divided by **scale**. MQTT topics are relative to `MQTT_TOPIC_PREFIX` (default `anker`). Fields without an MQTT topic are dump-only.

Sign conventions below describe the **raw signed register**, which is what the gateway and dump tools publish. Positive/negative meanings are not always the same across fields.

## Device

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `device_model` | 32768 | STRING | 5 | 1 | - | `device/model` |
| `device_model_2` | 10090 | STRING | 3 | 1 | - | - |
| `device_sn` | 10100 | STRING | 12 | 1 | - | `device/sn` |
| `device_sw_version` | 10112 | STRING | 6 | 1 | - | `device/sw_version` |
| `device_sw_version_LE` | 10118 | STRING_LE | 5 | 1 | - | - |
| `system_time` | 10060 | UINT32 | 2 | 1 | s | `device/system_time` |

- `device_model_2` is an alias of `device_model` (register 32768).
- `device_sw_version_LE` is the software version with bytes swapped inside each 16-bit register.
- `system_time` is seconds since 1970-01-01 00:00:00 UTC.

## Status

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `battery_status` | 10001 | UINT16 | 1 | 1 | - | `status/battery_status` |
| `ems_mode_mask` | 32774 | UINT16 | 1 | 1 | - | `status/ems_mode_mask` |

`ems_mode_mask` is a capability bitmask for operational modes (register 0x8006). Each set bit means that `operating_mode` is available:

| `operating_mode` | Bit | Mask |
| --- | ---: | ---: |
| 0 `self_consumption` | 0 | 1 |
| 1 `tou_mode` | 1 | 2 |
| 2 `rapid_charge` | - | - |
| 3 `third_party_control` | 5 | 32 |
| 4 `custom_mode` | 2 | 4 |
| 5 `socket_overlay_mode` | 4 | 16 |
| 6 `smart_mode` | 3 | 8 |
| 7 `dynamic_pricing` | 6 | 64 |

Exact bit mapping is from the official Home Assistant integration. `rapid_charge` has no capability bit: `ems_mode_mask` does not change when that mode is used.

Observed values:

- `36` (bits 2+5): `custom_mode` and `third_party_control`
- `111` (bits 0+1+2+3+5+6, with smart meter): `self_consumption`, `tou_mode`, `custom_mode`, `smart_mode`, `third_party_control`, `dynamic_pricing`

## Battery

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `battery_soc` | 10014 | UINT16 | 1 | 1 | % | `battery/curr/battery_soc` |
| `battery_soc_2` | 10256 | UINT16 | 1 | 1 | % | - |
| `battery_soh` | 10015 | UINT16 | 1 | 1 | % | `battery/curr/battery_soh` |
| `battery_power` | 10008 | INT32 | 2 | 1 | W | `battery/curr/battery_power` |
| `battery_internal_power` | 10254 | INT32 | 2 | 1 | W | `battery/curr/battery_internal_power` |
| `rated_energy` | 10250 | UINT32 | 2 | 10 | kWh | `battery/cfg/rated_energy` |
| `max_charge_power` | 10036 | INT32 | 2 | 1 | W | `battery/cfg/max_charge_power` |
| `max_discharge_power` | 10038 | INT32 | 2 | 1 | W | `battery/cfg/max_discharge_power` |

- `battery_soc_2` is likely a duplicate of `battery_soc`.
- `battery_soh` is likely state of health in %. **TODO: confirm.**
- `battery_power` is the battery's reported power flow. Positive: discharging. Negative: charging.
- `battery_internal_power` is the corresponding power measured closer to the battery internally, including conversion losses. Positive: charging. Negative: discharging. **TODO: confirm whether self-consumption is included.**
- `rated_energy` is the rated battery capacity shown in the app.
- `max_charge_power` and `max_discharge_power` are the values shown in the app under "Grid power limits". They are **grid** limits (max power from/to the grid), not device charge/discharge or import/export limits. The device can still charge using the configured export power limit. Writes to these registers have not succeeded. **TODO: the export power limit does not appear to be exposed over Modbus.**

## Current power

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `pv_power` | 10002 | INT32 | 2 | 1 | W | `power/curr/pv_power` |
| `third_party_pv_power` | 10004 | INT32 | 2 | 1 | W | `power/curr/third_party_pv_power` |
| `load_power` | 10010 | INT32 | 2 | 1 | W | `power/curr/load_power` |
| `grid_power` | 10012 | INT32 | 2 | 1 | W | `power/curr/grid_power` |
| `ac_grid_output_power` | 10208 | INT32 | 2 | 1 | W | `power/curr/ac_grid_output_power` |

- `load_power` is the current house load (sum of phases that are importing). Intended for use with an external power meter. **TODO: check if UINT32 is sufficient.**
- `grid_power` is current grid import/export (sum of all phases). Positive: importing. Negative: exporting. Intended for use with an external power meter.
- `ac_grid_output_power` is inverter AC output (`pv_power` + `battery_power`). **TODO: confirm whether this is output-only, and whether UINT32 is sufficient.**

## Energy counters

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `pv_total_generation` | 10018 | UINT32 | 2 | 10 | kWh | `power/cnt/pv_total_generation` |
| `load_total` | 10026 | UINT32 | 2 | 10 | kWh | `power/cnt/load_total` |
| `grid_export_total` | 10030 | UINT32 | 2 | 10 | kWh | `power/cnt/grid_export_total` |
| `ac_grid_energy_total` | 10034 | UINT32 | 2 | 10 | kWh | `power/cnt/ac_grid_energy_total` |
| `battery_charge_total` | 10022 | UINT32 | 2 | 10 | kWh | `power/cnt/battery_charge_total` |
| `charge_energy_total` | 10262 | UINT32 | 2 | 10 | kWh | `power/cnt/charge_energy_total` |
| `discharge_energy_total` | 10264 | UINT32 | 2 | 10 | kWh | `power/cnt/discharge_energy_total` |

- `pv_total_generation` is solar energy, shown as PV usage in the app. Register 10187 appears to be an alias.
- `load_total` is energy that went into the house, shown as home usage in the app.
- `grid_export_total` is energy exported to the grid, shown as grid export in the app.
- `ac_grid_energy_total` is total AC energy produced by the inverter. It is usually slightly higher than `grid_export_total`. **TODO: confirm.**
- `charge_energy_total` is likely an alias of `battery_charge_total`.
- There is no `grid_import_total` register. It is likely:

  load_total + battery_charge_total + grid_export_total − pv_total_generation − discharge_energy_total

## PV strings

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `pv1_voltage` | 10167 | INT16 | 1 | 10 | V | `pv/1/voltage` |
| `pv1_current` | 10168 | INT16 | 1 | 100 | A | `pv/1/current` |
| `pv2_voltage` | 10169 | INT16 | 1 | 10 | V | `pv/2/voltage` |
| `pv2_current` | 10170 | INT16 | 1 | 100 | A | `pv/2/current` |
| `pv3_voltage` | 10171 | INT16 | 1 | 10 | V | `pv/3/voltage` |
| `pv3_current` | 10172 | INT16 | 1 | 100 | A | `pv/3/current` |
| `pv4_voltage` | 10173 | INT16 | 1 | 10 | V | `pv/4/voltage` |
| `pv4_current` | 10174 | INT16 | 1 | 100 | A | `pv/4/current` |

Voltage and current are signed. At night the inverter reports small negative ADC offsets; decoding them as unsigned produces nonsense values such as 655 A.

PV1–3 at `10167–10172` are confirmed on this E5000 Pro (FW 1.0.2.30). The gateway still publishes `pv/4/*` from `10173`/`10174`, but those reads are **not a live fourth string** (always 0 while the Anker app shows PV4). See [README](./README.md#discoveriesbugs).

This firmware exposes PV1–3 as a **closed 6-register object**: every address `10167`–`10172` is a valid read start; **`10173` is not**. That is the same rule as other implemented scalars (`10156` temperature, `10183`, `10187`). So this is not “PV4 exists but needs a different count from `10167`”. The PCS string table on Modbus ends after three V/I pairs.

Those six registers sit inside the SOLIX X1 8-string V/I map (`10167`–`10182`). On X1, PV4 is `10173`/`10174` and total PV is INT32 at `10183`. On this E5000 Pro:

- `10173`/`10174` (X1 PV4) and `10175`–`10182` (X1 PV5–8) are unimplemented (invalid start → exception 2; batched reads return silent zeros). Same firmware behavior the official HA AE103 yaml documents for `0x8007` (`parallel_capability_mask`): a batch that spans an unimplemented register appends a silent zero, while a dedicated read of that address returns Illegal Data Address, so the two cases cannot be distinguished ([`58f0132b…yaml` L27–L31](https://github.com/anker-charging/ha-anker-solix-official/blob/main/custom_components/anker_solix_official/config/58f0132b5f7979b2cfa43a0eb1fca770053288032386ff6a4da5ed2d72d4ea35.yaml#L27-L31)).
- X1 `10130` “number of MPPTs” reads `21505`, not `4`.
- X1 `10183` “total PV power” INT32 stays `140`–`150` and does **not** track `pv_power` (`10002`) or the PV1–3 `V*I` gap. The low word behaves like `14.0`–`15.0` V (pack nominal is 16 VDC).
- Official Anker HA for E5000 / Max / Max AC never publishes per-string PV. It skips `10157`–`10207` entirely. Four-channel Solarbank telemetry elsewhere is **watt channels** (`solar_power_1`…`solar_power_4` on SB2 Pro / SB3 cloud MQTT), not this V/I table.

Input vs holding match. No fourth 16–50 V pair in `10000`–`10800`, `10632`–`10773`, `32768`–`32820`, or `60000`–`60124`. `pv_power` is ~10–40 W above PV1–3 `V*I` (10 W resolution); no other register tracked that remainder as PV4 power.

**TODO:** PV4 is visible in the Anker app / cloud path; it is not in this Modbus map on FW 1.0.2.30. Do not treat MQTT `pv/4/*` as a live string until a register is found.

Derived (not read from Modbus):

| Field | MQTT | Notes |
| --- | --- | --- |
| `pv1_power` … `pv4_power` | `pv/1/power` … `pv/4/power` | `round(voltage * current, 2)` |
| `pv_power_derived` | `power/curr/pv_power_derived` | Sum of the four PV string powers |

## Grid

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `grid_voltage` | 10199 | UINT16 | 1 | 10 | V | `grid/voltage` |
| `phase_a_voltage` | 10202 | UINT16 | 1 | 10 | V | `grid/phase_a_voltage` |
| `grid_current` | 10205 | UINT16 | 1 | 100 | A | `grid/current` |
| `grid_frequency` | 10213 | UINT16 | 1 | 100 | Hz | `grid/frequency` |
| `backup_grid_frequency` | 10238 | UINT16 | 1 | 100 | Hz | `grid/backup_frequency` |

On the SOLIX X1, `phase_a_voltage` depends on the operating mode. On the SOLIX E5000 Pro it appears to always match `grid_voltage`.

Registers 10212 and 10237 also look like grid-frequency values.

No valid power-factor register has been found. **TODO: confirm whether the inverter exposes one.**

## Temperature

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `internal_temperature` | 10156 | INT16 | 1 | 10 | °C | `temperature/internal` |

Also referred to as battery temperature.

## Control

These holding registers are writable. The gateway currently only reads them back.

| Field | Register | Type | Count | Scale | Unit | MQTT |
| --- | ---: | --- | ---: | ---: | --- | --- |
| `operating_mode` | 10064 | UINT16 | 1 | 1 | - | `control/operating_mode` |
| `battery_power_setpoint` | 10071 | INT32 | 2 | 1 | W | `control/battery_power_setpoint` |
| `battery_charge_limit` | 60000 | UINT16 | 1 | 1 | % | `control/battery_charge_limit` |
| `battery_discharge_limit` | 60001 | UINT16 | 1 | 1 | % | `control/battery_discharge_limit` |
| `battery_reserve_limit` | 60002 | UINT16 | 1 | 1 | % | `control/battery_reserve_limit` |
| `battery_reserve_enable` | 60003 | UINT16 | 1 | 1 | - | `control/battery_reserve_enable` |

`operating_mode`:

| Value | Mode |
| ---: | --- |
| 0 | `self_consumption` |
| 1 | `tou_mode` |
| 2 | `rapid_charge` |
| 3 | `third_party_control` |
| 4 | `custom_mode` |
| 5 | `socket_overlay_mode` |
| 6 | `smart_mode` |
| 7 | `dynamic_pricing` |

- `battery_power_setpoint` is valid in `third_party_control` (value 3). Positive: discharging. Negative: charging. Home Assistant documents the range as +–10000. Values in 0–99 W also affect control accuracy.
- `battery_reserve_limit` is only applied when `battery_reserve_enable` is set.
- `battery_reserve_enable` is named `backup_soc_enable` in official docs. `0` = disabled, `1` = enabled. Confirmed writable.

The load port does not appear to be controllable via Modbus. Register 10229 is `9` when the load port is active.

Export/import power-limit control mode and value, and Com disconnect time with VPP, are ignored for now. **TODO: find the export power limit register**; it is not `max_charge_power` / `max_discharge_power` (those are grid from/to limits) and does not appear to be exposed over Modbus.

## Official dump aliases

`tools/dump_modbus_official.py` uses a few official Home Assistant names for the same registers:

| Official name | Unofficial name |
| --- | --- |
| `cumulative_charge_energy` | `charge_energy_total` |
| `cumulative_discharge_energy` | `discharge_energy_total` |
| `backup_soc_enable` | `battery_reserve_enable` |

## Unknown non-zero registers

These addresses have been observed as non-zero and are not mapped yet. `tools/full_dump_modbus.py` still exports them in several encodings.

- 10040
- 10041 (bitmask?)
- 10059 (constant?)
- 10063
- 10070
- 10073 / 10074
- 10075 / 10076 (constant?)
- 10089 (bitmask?)
- 10099 (bitmask?)
- 10123 / 10124 (bitmask?)
- 10125 (bitmask?)
- 10129 / 10130
- 10132 / 10133 (constant?)
- 10166
- 10184 (14–16 V; likely battery pack voltage, not PV4)
- 10223 / 10224
- 10226 / 10227
- 10229 / 10230 (see load port note above)
- 10233 / 10234
- 10252
- 10253
