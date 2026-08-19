from __future__ import annotations

import logging

from pymodbus.client import ModbusTcpClient

from calculations import add_derived_values
from constants import FIELD_SPECS, REGISTER_RANGES, FieldSpec

LOG = logging.getLogger(__name__)


class ModbusReadError(RuntimeError):
    pass


class ModbusSnapshotReader:
    def __init__(self, host: str, port: int, timeout_seconds: float) -> None:
        LOG.debug(f"Initializing ModbusSnapshotReader for {host}:{port} with timeout {timeout_seconds}s")
        self._client = ModbusTcpClient(host, port=port, timeout=timeout_seconds)
        self._host = host
        self._port = port

    def close(self) -> None:
        LOG.debug("Closing Modbus client")
        self._client.close()

    def reconnect(self) -> None:
        LOG.info(f"Reconnecting to Modbus at {self._host}:{self._port}")
        self.close()
        if not self._client.connect():
            LOG.error(f"Could not connect to {self._host}:{self._port}")
            raise ModbusReadError(f"Could not connect to {self._host}:{self._port}")
        LOG.debug(f"Reconnected to Modbus at {self._host}:{self._port}")

    def read_snapshot(self) -> dict[str, object]:
        if not self._client.connected:
            LOG.debug(f"Connecting to Modbus at {self._host}:{self._port}")
            if not self._client.connect():
                LOG.error(f"Could not connect to {self._host}:{self._port}")
                raise ModbusReadError(f"Could not connect to {self._host}:{self._port}")
            LOG.debug(f"Connected to Modbus at {self._host}:{self._port}")
        else:
            LOG.debug(f"Already connected to Modbus at {self._host}:{self._port}")

        registers: dict[int, int] = {}

        for register_type, start, end in REGISTER_RANGES:
            count = end - start + 1
            LOG.debug(f"Reading {register_type} registers {start}-{end} (count={count})")

            response = self._read_block(register_type, start, count)

            if response.isError():
                LOG.error(f"Failed reading {register_type} registers {start}-{end}")
                raise ModbusReadError(f"Failed reading {register_type} registers {start}-{end}")
            
            LOG.debug(f"Successfully read {len(response.registers)} values from {register_type} registers {start}-{end}")

            for index, value in enumerate(response.registers):
                registers[start + index] = value

        snapshot = {spec.key: self._decode_field(spec, registers) for spec in FIELD_SPECS}
        return add_derived_values(snapshot)

    def _read_block(self, register_type: str, start: int, count: int):
        if register_type == "input":
            return self._client.read_input_registers(start, count=count)
        return self._client.read_holding_registers(start, count=count)

    @staticmethod
    def _decode_field(spec: FieldSpec, registers: dict[int, int]) -> object:
        if spec.register_type == "UINT16":
            value = _u16(registers, spec.address)
        elif spec.register_type == "INT16":
            value = _s16(registers, spec.address)
        elif spec.register_type == "UINT32":
            value = _u32(registers, spec.address)
        elif spec.register_type == "INT32":
            value = _s32(registers, spec.address)
        elif spec.register_type == "STRING":
            value = _string(registers, spec.address, spec.count)
        else:
            value = None

        if isinstance(value, (int, float)) and spec.scale != 1:
            value = value / spec.scale

        return value


def _u16(registers: dict[int, int], address: int) -> int | None:
    return registers.get(address)


def _s16(registers: dict[int, int], address: int) -> int | None:
    value = _u16(registers, address)
    if value is None:
        return None
    return value - 0x10000 if value >= 0x8000 else value


def _u32(registers: dict[int, int], address: int) -> int | None:
    high = registers.get(address)
    low = registers.get(address + 1)
    if high is None or low is None:
        return None
    return (high << 16) | low


def _s32(registers: dict[int, int], address: int) -> int | None:
    value = _u32(registers, address)
    if value is None:
        return None
    return value - 0x100000000 if value >= 0x80000000 else value


def _string(registers: dict[int, int], address: int, count: int) -> str | None:
    chars: list[str] = []

    for offset in range(count):
        register = registers.get(address + offset)
        if register is None:
            return None

        chars.append(chr((register >> 8) & 0xFF))
        chars.append(chr(register & 0xFF))

    return "".join(chars).rstrip("\x00").strip()
