from __future__ import annotations

import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from constants import PUBLISH_POINTS

LOG = logging.getLogger(__name__)


class MqttPublishError(RuntimeError):
    pass


class MqttGateway:
    def __init__(
        self,
        host: str,
        port: int,
        client_id: str,
        topic_prefix: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        LOG.debug(f"Initializing MqttGateway for {host}:{port} with client_id={client_id}, topic_prefix={topic_prefix}")
        self._host = host
        self._port = port
        self._topic_prefix = topic_prefix.rstrip("/")
        self._client = mqtt.Client(client_id=client_id)

        if username and password:
            LOG.debug(f"Setting MQTT credentials for user {username}")
            self._client.username_pw_set(username=username, password=password)

        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    def connect(self) -> None:
        LOG.debug(f"Connecting to MQTT broker at {self._host}:{self._port}")
        result = self._client.connect(self._host, self._port, keepalive=60)
        if result != mqtt.MQTT_ERR_SUCCESS:
            LOG.error(f"Could not connect to MQTT broker {self._host}:{self._port}")
            raise MqttPublishError(f"Could not connect to MQTT broker {self._host}:{self._port}")
        LOG.debug(f"Connected to MQTT broker at {self._host}:{self._port}")
        self._client.loop_start()

    def close(self) -> None:
        LOG.debug("Closing MQTT connection")
        try:
            self._client.loop_stop()
        finally:
            self._client.disconnect()
        LOG.debug("MQTT connection closed")

    def publish_snapshot(self, snapshot: dict[str, object]) -> None:
        LOG.debug(f"Publishing snapshot with {len(snapshot)} fields")
        for topic_suffix, key in PUBLISH_POINTS:
            self._publish_value(topic_suffix, snapshot.get(key))

        self._publish_value("status/online", True)
        self._publish_value("status/last_sync_ts", round(datetime.now(timezone.utc).timestamp(), 3))
        LOG.debug("Snapshot published")

    def publish_offline(self) -> None:
        self._publish_value("status/online", False)
        self._publish_value("status/battery_status", "offline")

    def _publish_value(self, topic_suffix: str, value: object) -> None:
        if value is None:
            LOG.debug(f"Skipping publish for {topic_suffix}: value is None")
            return

        topic = f"{self._topic_prefix}/{topic_suffix}"
        payload = _encode_payload(value)
        LOG.debug(f"Publishing {topic_suffix}={payload}")
        info = self._client.publish(topic, payload=payload, qos=1, retain=True)

        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            LOG.error(f"Failed to publish {topic}")
            raise MqttPublishError(f"Failed to publish {topic}")

        info.wait_for_publish()


def _encode_payload(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)