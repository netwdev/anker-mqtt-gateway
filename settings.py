from dataclasses import dataclass
import logging
import os

from dotenv import load_dotenv

LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    reader_host: str
    reader_port: int
    reader_timeout_seconds: float
    mqtt_host: str
    mqtt_port: int
    mqtt_client_id: str
    mqtt_username: str | None
    mqtt_password: str | None
    mqtt_topic_prefix: str
    poll_interval_seconds: float
    reconnect_delay_seconds: float


def load_settings() -> Settings:
    LOG.debug("Loading settings from environment variables")
    load_dotenv()

    reader_host = os.getenv("reader_host")
    mqtt_host = os.getenv("MQTT_HOST")

    if not reader_host:
        LOG.error("reader_host is required")
        raise RuntimeError("reader_host is required")

    if not mqtt_host:
        LOG.error("MQTT_HOST is required")
        raise RuntimeError("MQTT_HOST is required")

    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")

    if bool(mqtt_username) != bool(mqtt_password):
        LOG.error("MQTT_USERNAME and MQTT_PASSWORD must be set together")
        raise RuntimeError("MQTT_USERNAME and MQTT_PASSWORD must be set together")

    settings = Settings(
        reader_host=reader_host,
        reader_port=int(os.getenv("reader_port", "502")),
        reader_timeout_seconds=float(os.getenv("reader_timeout_seconds", "5")),
        mqtt_host=mqtt_host,
        mqtt_port=int(os.getenv("MQTT_PORT", "1883")),
        mqtt_client_id=os.getenv("MQTT_CLIENT_ID", "anker-gateway"),
        mqtt_username=mqtt_username,
        mqtt_password=mqtt_password,
        mqtt_topic_prefix=os.getenv("MQTT_TOPIC_PREFIX", "anker"),
        poll_interval_seconds=float(os.getenv("POLL_INTERVAL_SECONDS", "5")),
        reconnect_delay_seconds=float(os.getenv("RECONNECT_DELAY_SECONDS", "2")),
    )
    LOG.debug(f"Settings loaded: reader={settings.reader_host}:{settings.reader_port}, mqtt={settings.mqtt_host}:{settings.mqtt_port}, poll_interval={settings.poll_interval_seconds}s, reconnect_delay={settings.reconnect_delay_seconds}s")
    return settings