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
    ("input", 10124, 10248),        # note: intersects with 10000-10124
    ("input", 10250, 10374),
    ("input", 10632, 10747),
    ("input", 10648, 10772),        # note: intersects with 10632-10747
    ("input", 10649, 10773),        # note: intersects with 10648-10772
    ("input", 32768, 32892),
    ("input", 32774, 32898),        # note: intersects with 32768-32892
    ("input", 60000, 60124),
    ("input", 60003, 60127),        # note: intersects with 60000-60124

    ("holding", 10000, 10124),
    ("holding", 10124, 10248),        # note: intersects with 10000-10124
    ("holding", 10250, 10374),
    ("holding", 10632, 10747),
    ("holding", 10648, 10772),        # note: intersects with 10632-10747
    ("holding", 10649, 10773),        # note: intersects with 10648-10772
    ("holding", 32768, 32892),
    ("holding", 32774, 32898),        # note: intersects with 32768-32892
    ("holding", 60000, 60124),
    ("holding", 60003, 60127),        # note: intersects with 60000-60124
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

def string_le(addr, count):
    chars = []

    for i in range(count):
        reg = u16(addr + i)
        if reg is None:
            return None

        # Swap the two bytes within each 16-bit register
        chars.append(chr(reg & 0xFF))
        chars.append(chr((reg >> 8) & 0xFF))

    return "".join(chars).rstrip("\x00").strip()

# ---------------------------------------------------------------------
# Register definitions
# ---------------------------------------------------------------------

FIELDS = [
    # =======================================================================
    # Read Quantities Configuration (Sensor Type)
    # =======================================================================

    ("device_model", 32768, "STRING", 5, 1),
    ("device_sn", 10100, "STRING", 12, 1),
    ("device_sw_version", 10112, "STRING", 6, 1),

    ("battery_status", 10001, "UINT16", 1, 1),
    ("battery_soc", 10014, "UINT16", 1, 1),
    ("battery_soh", 10015, "UINT16", 1, 1),
    ("battery_power", 10008, "INT32", 2, 1),
    ("battery_internal_power", 10254, "INT32", 2, 1),
    ("battery_soc_2", 10256, "UINT16", 1, 1),

    ("pv_power", 10002, "INT32", 2, 1),
    ("third_party_pv_power", 10004, "INT32", 2, 1),

    ("load_power", 10010, "INT32", 2, 1),
    ("grid_power", 10012, "INT32", 2, 1),

    ("ac_grid_output_power", 10208, "INT32", 2, 1),

    ("pv_total_generation", 10018, "UINT32", 2, 10),
    ("load_total", 10026, "UINT32", 2, 10),
    ("grid_export_total", 10030, "UINT32", 2, 10),
    ("ac_grid_energy_total", 10034, "UINT32", 2, 10),
    ("battery_charge_total", 10022, "UINT32", 2, 10),
    ("charge_energy_total", 10262, "UINT32", 2, 10),
    ("discharge_energy_total", 10264, "UINT32", 2, 10),

    ("rated_energy", 10250, "UINT32", 2, 10),

    ("max_charge_power", 10036, "INT32", 2, 1),
    ("max_discharge_power", 10038, "INT32", 2, 1),

    ("ems_mode_mask", 32774, "UINT16", 1, 1),

    ("device_model_2", 10090, "STRING", 3, 1),
    ("device_sw_version_LE", 10118, "STRING_LE", 5, 1),

    ("internal_temperature", 10156, "INT16", 1, 10),

    ("pv1_voltage", 10167, "INT16", 1, 10),
    ("pv1_current", 10168, "INT16", 1, 100),
    ("pv2_voltage", 10169, "INT16", 1, 10),
    ("pv2_current", 10170, "INT16", 1, 100),
    ("pv3_voltage", 10171, "INT16", 1, 10),
    ("pv3_current", 10172, "INT16", 1, 100),
    ("pv4_voltage", 10173, "INT16", 1, 10),
    ("pv4_current", 10174, "INT16", 1, 100),

    ("grid_current", 10205, "UINT16", 1, 100),
    ("grid_frequency", 10213, "UINT16", 1, 100),
    ("backup_grid_frequency", 10238, "UINT16", 1, 100),
    ("grid_voltage", 10199, "UINT16", 1, 10),
    ("phase_a_voltage", 10202, "UINT16", 1, 10),

    ("system_time", 10060, "UINT32", 2, 1),

    # =======================================================================
    # Write Quantities Configuration (Control Type)
    # =======================================================================

    ("operating_mode", 10064, "UINT16", 1, 1),
    ("battery_power_setpoint", 10071, "INT32", 2, 1),
    ("battery_charge_limit", 60000, "UINT16", 1, 1),
    ("battery_discharge_limit", 60001, "UINT16", 1, 1),
    ("battery_reserve_limit", 60002, "UINT16", 1, 1),
    ("battery_reserve_enable", 60003, "UINT16", 1, 1),
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

    elif dtype == "STRING_LE":
        value = string_le(addr, count)

    else:
        value = None

    if isinstance(value, (int, float)) and gain != 1:
        value = value / gain

    result[name] = value

for pv_index in (1, 2, 3, 4):
    voltage = result.get(f"pv{pv_index}_voltage")
    current = result.get(f"pv{pv_index}_current")

    if isinstance(voltage, (int, float)) and isinstance(current, (int, float)):
        result[f"pv{pv_index}_power"] = round(voltage * current, 2)

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
