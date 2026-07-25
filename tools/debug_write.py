from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient
import os

load_dotenv()

HOST = os.getenv("MODBUS_HOST", "192.168.1.100")
PORT = int(os.getenv("MODBUS_PORT", "502"))
UNIT_ID = 1

client = ModbusTcpClient(HOST, port=PORT, timeout=5)

def write_int32(client, register, value):
    # Big-endian word order
    if value < 0:
        value &= 0xFFFFFFFF

    registers = [
        (value >> 16) & 0xFFFF,
        value & 0xFFFF,
    ]

    result = client.write_registers(
        address=register - 1,   # Modbus addresses are zero-based
        values=registers,
        device_id=UNIT_ID,
    )

    if result.isError():
        print(f"Failed writing {register}: {result}")
    else:
        print(f"Wrote {value} to register {register}")


def read_int32(client, register):
    result = client.read_holding_registers(
        address=register - 1,
        count=2,
        device_id=UNIT_ID,
    )

    if result.isError():
        print(result)
        return None

    value = (result.registers[0] << 16) | result.registers[1]

    if value & 0x80000000:
        value -= 0x100000000

    return value


client = ModbusTcpClient(HOST, port=PORT)

if not client.connect():
    raise RuntimeError(f"Could not connect to {HOST}:{PORT}")


REGISTER_MAX_CHARGE = 10036
REGISTER_MAX_DISCHARGE = 10038

print("Before:")
print("Charge     :", read_int32(client, REGISTER_MAX_CHARGE))
print("Discharge  :", read_int32(client, REGISTER_MAX_DISCHARGE))

write_int32(client, REGISTER_MAX_CHARGE, 1000)
write_int32(client, REGISTER_MAX_DISCHARGE, 800)

print("\nAfter:")
print("Charge     :", read_int32(client, REGISTER_MAX_CHARGE))
print("Discharge  :", read_int32(client, REGISTER_MAX_DISCHARGE))

client.close()
