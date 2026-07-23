# MQTT Gateway Template

MQTT Gateway Template is a Python application that reads data from a source (e.g., a Modbus device) and publishes it to an MQTT broker. It is designed to be easily configurable and extendable.

## MQTT topics

- `xy/device/model`

All published values are retained.

## Configuration

Set these environment variables before starting the gateway:

- `READER_HOST` required
- `READER_PORT` optional, default `502`
- `READER_TIMEOUT_SECONDS` optional, default `5`
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
python main.py
```
