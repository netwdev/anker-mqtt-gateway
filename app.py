from __future__ import annotations

import logging
import math
import signal
import time

from modbus_reader import ModbusReadError, ModbusSnapshotReader
from mqtt_gateway import MqttGateway, MqttPublishError
from settings import load_settings

# Configure logging
logging.basicConfig(
    encoding='utf-8', 
    level=logging.INFO,
    format='%(asctime)s - %(levelname)-8s - %(module)-15s - %(message)s'
)
LOG = logging.getLogger(__name__)


def main() -> None:
	LOG.info("Starting Anker Gateway")
	settings = load_settings()
	LOG.debug(f"Configuration loaded: modbus={settings.modbus_host}:{settings.modbus_port}, mqtt={settings.mqtt_host}:{settings.mqtt_port}")
	reader = ModbusSnapshotReader(
		settings.modbus_host,
		settings.modbus_port,
		settings.modbus_timeout_seconds,
	)
	LOG.debug("ModbusSnapshotReader initialized")
	publisher = MqttGateway(
		settings.mqtt_host,
		settings.mqtt_port,
		settings.mqtt_client_id,
		settings.mqtt_topic_prefix,
		settings.mqtt_username,
		settings.mqtt_password,
	)
	LOG.debug("MqttGateway initialized")

	stop_requested = False

	def handle_signal(_signum: int, _frame: object) -> None:
		nonlocal stop_requested
		LOG.info(f"Received signal {_signum}, shutting down gracefully")
		stop_requested = True

	signal.signal(signal.SIGINT, handle_signal)
	signal.signal(signal.SIGTERM, handle_signal)

	try:
		LOG.info("Connecting to MQTT broker")
		publisher.connect()
		LOG.info("Connected to MQTT broker")

		LOG.info(f"Starting main loop with poll interval {settings.poll_interval_seconds}s")
		next_run_time = math.ceil(time.monotonic())
		while not stop_requested:
			current_time = time.monotonic()
			if current_time < next_run_time:
				sleep_duration = next_run_time - current_time
				LOG.debug(f"Waiting {sleep_duration:.3f}s until the next scheduled run")
				time.sleep(sleep_duration)

			LOG.debug("Polling Modbus for snapshot")
			try:
				snapshot = reader.read_snapshot()
				LOG.debug(f"Snapshot read successfully with {len(snapshot)} fields")
			except ModbusReadError as exc:
				LOG.error(f"Modbus read failed: {exc}")
				LOG.info("Publishing offline status")
				try:
					publisher.publish_offline()
					LOG.debug("Offline status published")
				except MqttPublishError as mqtt_exc:
					LOG.error(f"MQTT publish failed while marking offline: {mqtt_exc}")
				LOG.info("Reconnecting to Modbus")
				reader.reconnect()
				LOG.debug("Modbus reconnected")
			else:
				LOG.debug("Publishing snapshot to MQTT")
				try:
					publisher.publish_snapshot(snapshot)
					LOG.info("Snapshot published successfully")
				except MqttPublishError as exc:
					LOG.error(f"MQTT publish failed: {exc}")
					LOG.info(
						f"Reconnecting to MQTT broker after {settings.reconnect_delay_seconds}s"
					)
					publisher.close()
					time.sleep(settings.reconnect_delay_seconds)
					publisher.connect()
					LOG.debug("MQTT broker reconnected")

			if not stop_requested:
				next_run_time += settings.poll_interval_seconds
	finally:
		LOG.info("Shutting down Anker Gateway")
		try:
			publisher.publish_offline()
			LOG.debug("Published offline status during shutdown")
		except Exception:
			pass
		reader.close()
		LOG.debug("Modbus reader closed")
		publisher.close()
		LOG.debug("MQTT publisher closed")
		LOG.info("Anker Gateway stopped")


if __name__ == "__main__":
	main()
