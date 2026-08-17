from dataclasses import dataclass
import logging
import os

from dotenv import load_dotenv

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    modbus_host: str
    modbus_port: int
    modbus_timeout_seconds: float
    mqtt_host: str
    mqtt_port: int
    mqtt_client_id: str
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_topic_prefix: str
    mqtt_qos: int
    mqtt_retain: bool
    poll_interval_seconds: float
    reconnect_delay_seconds: float


def load_settings() -> Settings:
    LOG.debug("Loading settings from environment variables")
    load_dotenv()

    modbus_host = os.getenv("MODBUS_HOST")
    mqtt_host = os.getenv("MQTT_HOST")

    if not modbus_host:
        LOG.error("MODBUS_HOST is required")
        raise RuntimeError("MODBUS_HOST is required")

    if not mqtt_host:
        LOG.error("MQTT_HOST is required")
        raise RuntimeError("MQTT_HOST is required")

    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")

    if bool(mqtt_username) != bool(mqtt_password):
        LOG.error("MQTT_USERNAME and MQTT_PASSWORD must be set together")
        raise RuntimeError("MQTT_USERNAME and MQTT_PASSWORD must be set together")

    try:
        mqtt_qos = int(os.getenv("MQTT_QOS", "1"))
        if mqtt_qos not in (0, 1, 2):
            raise ValueError
    except ValueError:
        LOG.error("MQTT_QOS must be 0, 1, or 2")
        raise RuntimeError("MQTT_QOS must be 0, 1, or 2") from None

    mqtt_retain_raw = os.getenv("MQTT_RETAIN", "true").strip().lower()
    if mqtt_retain_raw in ("1", "true", "yes"):
        mqtt_retain = True
    elif mqtt_retain_raw in ("0", "false", "no"):
        mqtt_retain = False
    else:
        LOG.error("MQTT_RETAIN must be true or false")
        raise RuntimeError("MQTT_RETAIN must be true or false")

    settings = Settings(
        modbus_host=modbus_host,
        modbus_port=int(os.getenv("MODBUS_PORT", "502")),
        modbus_timeout_seconds=float(os.getenv("MODBUS_TIMEOUT_SECONDS", "5")),
        mqtt_host=mqtt_host,
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "anker-gateway"),
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "anker"),
        mqtt_qos=mqtt_qos,
        mqtt_retain=mqtt_retain,
        poll_interval_seconds=float(os.getenv("POLL_INTERVAL_SECONDS", "5")),
        reconnect_delay_seconds=float(os.getenv("RECONNECT_DELAY_SECONDS", "2")),
    )
    LOG.debug(f"Settings loaded: modbus={settings.modbus_host}:{settings.modbus_port}, mqtt={settings.mqtt_host}:{settings.mqtt_port}, qos={settings.mqtt_qos}, retain={settings.mqtt_retain}, poll_interval={settings.poll_interval_seconds}s, reconnect_delay={settings.reconnect_delay_seconds}s")
    return settings