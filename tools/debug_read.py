from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient
import os

load_dotenv()

HOST = os.getenv("MODBUS_HOST", "192.168.1.100")
PORT = int(os.getenv("MODBUS_PORT", "502"))

client = ModbusTcpClient(HOST, port=PORT, timeout=5)

if not client.connect():
    raise RuntimeError("Could not connect")


def dump(label, address, count):
    print(f"\n=== {label} ===")
    print(f"Address={address}, Count={count}")

    try:
        rr = client.read_input_registers(
            address=address,
            count=count,
            device_id=1,
        )

        print("Type:", type(rr).__name__)

        if rr.isError():
            print("ERROR:", rr)
            print("Function code:", rr.function_code)
            if hasattr(rr, "exception_code"):
                print("Exception code:", rr.exception_code)
        else:
            print("Registers:", rr.registers)

    except Exception as e:
        print("Exception:", repr(e))



dump("32774", 32774, 125)


client.close()
