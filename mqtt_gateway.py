from __future__ import annotations

import logging
import threading
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
        qos: int = 1,
        retain: bool = True,
        last_will: bool = True,
    ) -> None:
        LOG.debug(f"Initializing MqttGateway for {host}:{port} with client_id={client_id}, topic_prefix={topic_prefix}, qos={qos}, retain={retain}, last_will={last_will}")
        self._host = host
        self._port = port
        self._topic_prefix = topic_prefix.rstrip("/")
        self._qos = qos
        self._retain = retain
        # MQTT 3.1.1 does not include a reason code in PUBACK packets, so a
        # broker can reject a publish because of its ACL without giving the
        # client enough information to report it. MQTT v5 does, including
        # 0x87 (Not authorized).
        self._client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv5,
        )
        self._publish_reason_codes: dict[int, object] = {}
        self._publish_reason_codes_lock = threading.Lock()
        self._client.on_publish = self._on_publish

        if username and password:
            LOG.debug(f"Setting MQTT credentials for user {username}")
            self._client.username_pw_set(username=username, password=password)

        if last_will:
            will_topic = f"{self._topic_prefix}/status/online"
            self._client.will_set(
                will_topic,
                payload=_encode_payload(False),
                qos=qos,
                retain=retain,
            )
            LOG.debug(f"MQTT last will set for {will_topic}")

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
        pending: list[tuple[str, mqtt.MQTTMessageInfo]] = []
        for topic_suffix, key in PUBLISH_POINTS:
            info = self._publish_value(topic_suffix, snapshot.get(key), wait=False)
            if info is not None:
                pending.append((topic_suffix, info))

        for topic_suffix, value in (
            ("status/online", True),
            ("status/last_sync_ts", round(datetime.now(timezone.utc).timestamp(), 3)),
        ):
            info = self._publish_value(topic_suffix, value, wait=False)
            if info is not None:
                pending.append((topic_suffix, info))

        for topic_suffix, info in pending:
            self._wait_for_publish(topic_suffix, info)
        LOG.debug("Snapshot published")

    def publish_offline(self) -> None:
        pending: list[tuple[str, mqtt.MQTTMessageInfo]] = []
        for topic_suffix, value in (
            ("status/online", False),
            ("status/battery_status", "offline"),
        ):
            info = self._publish_value(topic_suffix, value, wait=False)
            if info is not None:
                pending.append((topic_suffix, info))

        for topic_suffix, info in pending:
            self._wait_for_publish(topic_suffix, info)

    def _publish_value(
        self,
        topic_suffix: str,
        value: object,
        *,
        wait: bool = True,
    ) -> mqtt.MQTTMessageInfo | None:
        if value is None:
            LOG.debug(f"Skipping publish for {topic_suffix}: value is None")
            return None

        topic = f"{self._topic_prefix}/{topic_suffix}"
        payload = _encode_payload(value)
        LOG.debug(f"Publishing {topic_suffix}={payload}")
        info = self._client.publish(topic, payload=payload, qos=self._qos, retain=self._retain)

        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            LOG.error(f"Failed to publish {topic}")
            raise MqttPublishError(f"Failed to publish {topic}")

        if not wait:
            return info

        self._wait_for_publish(topic_suffix, info)

        return info

    def _wait_for_publish(self, topic_suffix: str, info: mqtt.MQTTMessageInfo) -> None:
        topic = f"{self._topic_prefix}/{topic_suffix}"
        try:
            info.wait_for_publish()
        except (RuntimeError, ValueError) as exc:
            LOG.error(f"Failed to publish {topic}: {exc}")
            raise MqttPublishError(f"Failed to publish {topic}: {exc}") from exc

        with self._publish_reason_codes_lock:
            reason_code = self._publish_reason_codes.pop(info.mid, None)

        if reason_code is not None and _reason_code_is_failure(reason_code):
            LOG.error(f"MQTT broker rejected publish to {topic}: {reason_code}")
            raise MqttPublishError(
                f"MQTT broker rejected publish to {topic}: {reason_code}"
            )

    def _on_publish(
        self,
        _client: mqtt.Client,
        _userdata: object,
        mid: int,
        reason_code: object,
        _properties: object,
    ) -> None:
        with self._publish_reason_codes_lock:
            self._publish_reason_codes[mid] = reason_code


def _encode_payload(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _reason_code_is_failure(reason_code: object) -> bool:
    """Return whether an MQTT v5 PUBACK reason code means rejection."""
    is_failure = getattr(reason_code, "is_failure", None)
    if is_failure is not None:
        return bool(is_failure)
    return int(reason_code) != 0
