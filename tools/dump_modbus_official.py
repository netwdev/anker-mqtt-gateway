"""
Dump all known registers from the Anker SOLIX Solarbank 4 E5000 Pro in JSON format.
"""

import json
import os
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

load_dotenv()

HOST = os.getenv("MODBUS_HOST")
PORT = int(os.getenv("MODBUS_PORT", "502"))

client = ModbusTcpClient(HOST, port=PORT)

if not client.connect():
    raise RuntimeError(f"Could not connect to {HOST}:{PORT}")

# ---------------------------------------------------------------------
# Batch ranges from the configuration
# ---------------------------------------------------------------------

RANGES = [
    ("input", 10000, 10050),
    ("input", 10090, 10156),
    ("input", 10208, 10265),
    ("input", 32768, 32774),

    ("holding", 10060, 10072),
    ("holding", 10074, 10081),
    ("holding", 60000, 60003),
]

registers = {}

for regtype, start, end in RANGES:
    count = end - start + 1

    if regtype == "input":
        rr = client.read_input_registers(start, count=count)
    else:
        rr = client.read_holding_registers(start, count=count)

    if rr.isError():
        print(f"Failed reading {regtype} {start}-{end}")
        continue

    for i, value in enumerate(rr.registers):
        registers[start + i] = value

client.close()

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def u16(addr):
    return registers.get(addr)


def s16(addr):
    v = registers.get(addr)
    if v is None:
        return None
    return v - 0x10000 if v >= 0x8000 else v


def u32(addr):
    hi = registers.get(addr)
    lo = registers.get(addr + 1)
    if hi is None or lo is None:
        return None
    return (hi << 16) | lo


def s32(addr):
    v = u32(addr)
    if v is None:
        return None
    if v >= 0x80000000:
        v -= 0x100000000
    return v


def string(addr, count):
    chars = []

    for i in range(count):
        reg = registers.get(addr + i)
        if reg is None:
            return None

        chars.append(chr((reg >> 8) & 0xFF))
        chars.append(chr(reg & 0xFF))

    return "".join(chars).rstrip("\x00").strip()


# ---------------------------------------------------------------------
# Register definitions
# ---------------------------------------------------------------------

FIELDS = [
    ("device_model", 32768, "STRING", 5, 1),
    ("device_sn", 10100, "STRING", 12, 1),
    ("device_sw_version", 10112, "STRING", 6, 1),

    ("battery_soc", 10014, "UINT16", 1, 1),

    ("pv_power", 10002, "INT32", 2, 1),
    ("third_party_pv_power", 10004, "INT32", 2, 1),

    ("battery_power", 10008, "INT32", 2, 1),

    ("load_power", 10010, "INT32", 2, 1),

    ("grid_power", 10012, "INT32", 2, 1),

    ("ac_grid_output_power", 10208, "INT32", 2, 1),

    ("pv_total_generation", 10018, "UINT32", 2, 10),

    ("cumulative_charge_energy", 10262, "UINT32", 2, 10),
    ("cumulative_discharge_energy", 10264, "UINT32", 2, 10),

    ("rated_energy", 10250, "UINT32", 2, 10),

    ("battery_status", 10001, "UINT16", 1, 1),

    ("max_charge_power", 10036, "INT32", 2, 1),
    ("max_discharge_power", 10038, "INT32", 2, 1),

    ("ems_mode_mask", 32774, "UINT16", 1, 1),

    ("backup_soc_enable", 60003, "UINT16", 1, 1),
]

result = {}

for name, addr, dtype, count, gain in FIELDS:

    if dtype == "UINT16":
        value = u16(addr)

    elif dtype == "INT16":
        value = s16(addr)

    elif dtype == "UINT32":
        value = u32(addr)

    elif dtype == "INT32":
        value = s32(addr)

    elif dtype == "STRING":
        value = string(addr, count)

    else:
        value = None

    if isinstance(value, (int, float)) and gain != 1:
        value = value / gain

    result[name] = value

print(json.dumps(result, indent=4))
