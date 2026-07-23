# Anker MQTT Gateway (unofficial)

This service polls the Anker inverter/device over Modbus TCP and publishes retained MQTT topics under the `anker/` prefix.

Currently supported devices:

- Anker SOLIX Solarbank 4 E5000 Pro

## MQTT topics

- `anker/device/model`
- `anker/device/sn`
- `anker/device/sw_version`
- `anker/power/curr/pv_power`
- `anker/power/curr/load_power`
- `anker/power/curr/grid_import_power`
- `anker/power/curr/grid_export_power`
- `anker/power/cnt/pv_total_generation`
- `anker/power/cnt/cumulative_charge_energy`
- `anker/power/cnt/cumulative_discharge_energy`
- `anker/power/cfg/max_charge_power`
- `anker/power/cfg/max_discharge_power`
- `anker/battery/curr/battery_soc`
- `anker/battery/curr/battery_charging_power`
- `anker/battery/curr/battery_discharging_power`
- `anker/battery/cfg/rated_energy`
- `anker/status/online`
- `anker/status/battery_status`
- `anker/status/last_sync_ts`

All published values are retained.

## Configuration

Set these environment variables before starting the gateway:

- `MODBUS_HOST` required
- `MODBUS_PORT` optional, default `502`
- `MODBUS_TIMEOUT_SECONDS` optional, default `5`
- `MQTT_HOST` required
- `MQTT_PORT` optional, default `1883`
- `MQTT_CLIENT_ID` optional, default `anker-gateway`
- `MQTT_USERNAME` optional
- `MQTT_PASSWORD` optional
- `MQTT_TOPIC_PREFIX` optional, default `anker`
- `POLL_INTERVAL_SECONDS` optional, default `5`
- `RECONNECT_DELAY_SECONDS` optional, default `2`

If `MQTT_USERNAME` is set, `MQTT_PASSWORD` must also be set.

## Run

```bash
python app.py
```

## References

Ranges and meaning of registers are based on the official home assistant integration for Anker SOLIX Solarbank 4 E5000 Pro:
https://github.com/anker-charging/ha-anker-solix-official/blob/main/custom_components/anker_solix_official/config/58f0132b5f7979b2cfa43a0eb1fca770053288032386ff6a4da5ed2d72d4ea35.yaml

It was tested on a Anker SOLIX Solarbank 4 E5000 Pro with firmware version 1.0.2.22.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for more information.
