"""
Dump all scanned registers from the Anker SOLIX Solarbank 4 E5000 Pro in JSON format.
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
    ("input", 10000, 10124),
    ("input", 10130, 10130),
    ("input", 10133, 10133),
    ("input", 10144, 10156),
    ("input", 10167, 10172),
    ("input", 10183, 10183),
    ("input", 10187, 10187),
    ("input", 10199, 10199),
    ("input", 10202, 10202),
    ("input", 10205, 10205),
    ("input", 10208, 10208),
    ("input", 10210, 10210),
    ("input", 10212, 10213),
    ("input", 10224, 10224),
    ("input", 10227, 10227),
    ("input", 10230, 10230),
    ("input", 10233, 10233),
    ("input", 10235, 10235),
    ("input", 10237, 10238),
    ("input", 10250, 10374),
    ("input", 10632, 10637),
    ("input", 10648, 10649),
    ("input", 32768, 32772),
    ("input", 32774, 32774),
    ("input", 60000, 60124),

    ("holding", 10000, 10124),
    ("holding", 10130, 10130),
    ("holding", 10133, 10133),
    ("holding", 10144, 10156),
    ("holding", 10167, 10172),
    ("holding", 10183, 10183),
    ("holding", 10187, 10187),
    ("holding", 10199, 10199),
    ("holding", 10202, 10202),
    ("holding", 10205, 10205),
    ("holding", 10208, 10208),
    ("holding", 10210, 10210),
    ("holding", 10212, 10213),
    ("holding", 10224, 10224),
    ("holding", 10227, 10227),
    ("holding", 10230, 10230),
    ("holding", 10233, 10233),
    ("holding", 10235, 10235),
    ("holding", 10237, 10238),
    ("holding", 10250, 10374),
    ("holding", 10632, 10637),
    ("holding", 10648, 10649),
    ("holding", 32768, 32772),
    ("holding", 32774, 32774),
    ("holding", 60000, 60124),
]

# ---------------------------------------------------------------------
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
    v = u16(addr)
    if v is None:
        return None
    return v - 0x10000 if v >= 0x8000 else v


# Big-endian word order (your current implementation)
def u32_be(addr):
    hi = u16(addr)
    lo = u16(addr + 1)
    if hi is None or lo is None:
        return None
    return (hi << 16) | lo


def s32_be(addr):
    v = u32_be(addr)
    if v is None:
        return None
    return v - 0x100000000 if v >= 0x80000000 else v


# Word-swapped (little-endian word order)
def u32_le(addr):
    lo = u16(addr)
    hi = u16(addr + 1)
    if hi is None or lo is None:
        return None
    return (hi << 16) | lo


def s32_le(addr):
    v = u32_le(addr)
    if v is None:
        return None
    return v - 0x100000000 if v >= 0x80000000 else v


def string(addr, count):
    chars = []

    for i in range(count):
        reg = u16(addr + i)
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

    ("battery_charging_power", 10008, "INT32", 2, 1),
    ("battery_discharging_power", 10008, "INT32", 2, 1),

    ("load_power", 10010, "INT32", 2, 1),

    ("grid_import_power", 10012, "INT32", 2, 1),
    ("grid_export_power", 10012, "INT32", 2, 1),

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

    ## Additional registers that are not part of the known/official fields
    ("?device_model?", 10090, "STRING", 3, 1),
    ("device_sw_version(in LE)?", 10118, "STRING", 5, 1),


]

known_registers = set()

for _, addr, _, count, _ in FIELDS:
    for i in range(count):
        known_registers.add(addr + i)

result = {}

for name, addr, dtype, count, gain in FIELDS:

    if dtype == "UINT16":
        value = u16(addr)

    elif dtype == "INT16":
        value = s16(addr)

    elif dtype == "UINT32":
        value = u32_be(addr)

    elif dtype == "INT32":
        value = s32_be(addr)

    elif dtype == "STRING":
        value = string(addr, count)

    else:
        value = None

    if isinstance(value, (int, float)) and gain != 1:
        value = value / gain

    # Split signed power sensors like the HA integration
    if name == "battery_charging_power":
        value = max(-value, 0)

    elif name == "battery_discharging_power":
        value = max(value, 0)

    elif name == "grid_import_power":
        value = max(value, 0)

    elif name == "grid_export_power":
        value = max(-value, 0)

    result[name] = value

# ---------------------------------------------------------------------
# Export every unknown register in all formats
# ---------------------------------------------------------------------

for addr in sorted(registers):

    if addr in known_registers:
        continue

    result[f"unknown_{addr}"] = {
        "u16": u16(addr),
        "s16": s16(addr),
        "u32_be": u32_be(addr),
        "s32_be": s32_be(addr),
        "u32_le": u32_le(addr),
        "s32_le": s32_le(addr),
    }

print(json.dumps(result, indent=4))
