from __future__ import annotations

import logging

LOG = logging.getLogger(__name__)


class ReadError(RuntimeError):
    pass

class SnapshotReader:
    def __init__(self, host: str, port: int, timeout_seconds: float) -> None:
        LOG.debug(f"Initializing SnapshotReader for {host}:{port} with timeout {timeout_seconds}s")
        self._client = None  # e.g. ModbusTcpClient(host, port=port, timeout=timeout_seconds)
        self._host = host
        self._port = port

    def close(self) -> None:
        ...

    def reconnect(self) -> None:
        ...

    def read_snapshot(self) -> dict[str, object]:
        ...
