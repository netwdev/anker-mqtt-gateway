# Anker MQTT Gateway (unofficial)

This service polls the Anker inverter/device over Modbus TCP and publishes retained MQTT topics under the `anker/` prefix by default.

Currently supported devices:

- Anker SOLIX Solarbank 4 E5000 Pro

## MQTT topics

Topics are prefixed with `MQTT_TOPIC_PREFIX`:

- `device/model`, `device/sn`, `device/sw_version`, `device/system_time`
- `status/online`, `status/battery_status`, `status/ems_mode_mask`, `status/last_sync_ts`
- `battery/curr/battery_soc`, `battery/curr/battery_soh`, `battery/curr/battery_power`, `battery/curr/battery_power_real`
- `battery/cfg/rated_energy`, `battery/cfg/max_charge_power`, `battery/cfg/max_discharge_power`
- `control/operating_mode`, `control/battery_power_setpoint`
- `control/battery_charge_limit`, `control/battery_discharge_limit`, `control/battery_reserve_limit`, `control/battery_reserve_enable`
- `power/curr/pv_power`, `power/curr/pv_power_derived`, `power/curr/third_party_pv_power`
- `power/curr/load_power`, `power/curr/grid_power`, `power/curr/ac_grid_output_power`
- `power/cnt/pv_total_generation`, `power/cnt/load_total`, `power/cnt/grid_export_total`
- `power/cnt/ac_grid_energy_total`, `power/cnt/battery_charge_total`, `power/cnt/charge_energy_total`, `power/cnt/discharge_energy_total`
- `pv/{1..4}/voltage`, `pv/{1..4}/current`, `pv/{1..4}/power`
- `grid/voltage`, `grid/current`, `grid/frequency`, `grid/backup_frequency`, `grid/phase_a_voltage`
- `temperature/internal`

All published values use the configured MQTT QoS (default 1). Messages are retained when `MQTT_RETAIN` is true (the default).
When `MQTT_LAST_WILL` is true (the default), the broker publishes `status/online=false` if the gateway disconnects unexpectedly.
Broker publish failures—including insufficient topic permissions—raise an error and trigger the MQTT reconnect path.

QoS 0 does not wait for a broker acknowledgement, so there is no check that the published data was received.

## Modbus polling

The configured reads are kept within Modbus's 125-register request limit and currently cover these ranges for both input and holding registers:

- `10000–10124`
- `10156–10265`
- `32768–32774`
- `60000–60003`

The gateway uses MQTT 5 so broker publish acknowledgements can report authorization failures (QoS 1 and 2 only).

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
- `MQTT_QOS` optional, default `1` (`0`, `1`, or `2`)
- `MQTT_RETAIN` optional, default `true`
- `MQTT_LAST_WILL` optional, default `true`
- `POLL_INTERVAL_SECONDS` optional, default `5`
- `RECONNECT_DELAY_SECONDS` optional, default `2`

If `MQTT_USERNAME` is set, `MQTT_PASSWORD` must also be set.

## Run

```bash
python app.py
```

## Docker

Build and run with the same environment variables listed in [Configuration](#configuration). `MODBUS_HOST` and `MQTT_HOST` are required.

```bash
docker build -t anker-mqtt-gateway .
docker run --rm \
  -e MODBUS_HOST=192.168.1.100 \
  -e MQTT_HOST=192.168.1.200 \
  anker-mqtt-gateway
```

Optional variables (`MODBUS_PORT`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_TOPIC_PREFIX`, `MQTT_QOS`, `MQTT_RETAIN`, `MQTT_LAST_WILL`, `POLL_INTERVAL_SECONDS`, and others) can be passed the same way with `-e`.

### Compose

Copy [`.env.sample`](./.env.sample) to `.env`, set at least `MODBUS_HOST` and `MQTT_HOST`, then:

```bash
docker compose up -d --build
```

The included [`compose.yaml`](./compose.yaml) builds the image and loads configuration from `.env`.

## References

Ranges and meaning of registers are based on the [official home assistant integration for Anker SOLIX Solarbank 4 E5000 Pro](https://github.com/anker-charging/ha-anker-solix-official/blob/main/custom_components/anker_solix_official/config/58f0132b5f7979b2cfa43a0eb1fca770053288032386ff6a4da5ed2d72d4ea35.yaml)

as well as the official Anker SOLIX X1 Series
Modbus Protocol Specification (V1.0.0) and awesome community projects like [afewyards X1 integration](https://github.com/afewyards/anker-x1-ha/) (`dashboard.py`, `coordinator.py`)

Many unknown registers were reverse-engineered.

## Compatibility

It was tested on a Anker SOLIX Solarbank 4 E5000 Pro with following firmware versions:

```
- 1.0.2.22
- 1.0.2.30
```

## Discoveries/Bugs

At least up to firmware version 1.0.2.30:

- The device is very strict about the start register on a modbus read request. Often a request with a bigger count and earlier start register is needed while a single count read of the same register fails. This is likely a bug in the device firmware.
  For example, reading register 32775 with a count of 1 fails, but reading register 32774 with a count of 2 succeeds.

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for more information.
