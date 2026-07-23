"""
Scan all registers (Modbus device ID 1) from the Anker SOLIX Solarbank 4 E5000 Pro and dump in JSON format.

Known issues:
- The success counter is reported incorrectly

"""

import json
import os
import signal
import sys
import time
from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

load_dotenv()

HOST = os.getenv("MODBUS_HOST", "192.168.1.100")
PORT = int(os.getenv("MODBUS_PORT", "502"))

BLOCK_SIZE = 125
MAX_ADDRESS = 65535
REQUEST_DELAY = 0.0000001       # avoid additional delays
SAVE_EVERY = 20

client = ModbusTcpClient(
    HOST,
    port=PORT,
    timeout=5
)

if not client.connect():
    raise RuntimeError(f"Unable to connect to {HOST}:{PORT}")

results = {"input": {}, "holding": {}}
stats = {"requests":0,"success":0,"failed":0}

def build_ranges(regs):
    addrs = sorted(int(k) for k in regs.keys())
    if not addrs:
        return []
    out=[]
    s=p=addrs[0]
    for a in addrs[1:]:
        if a==p+1:
            p=a
        else:
            out.append({"start":s,"end":p,"count":p-s+1})
            s=p=a
    out.append({"start":s,"end":p,"count":p-s+1})
    return out

def save():
    with open("modbus_dump.json","w") as f:
        json.dump({
            "ranges":{
                "input":build_ranges(results["input"]),
                "holding":build_ranges(results["holding"])
            },
            "registers":results,
            "stats":stats
        },f,indent=2)

def shutdown(sig=None,frame=None):
    print("\nSaving progress...")
    save()
    client.close()
    print("Done.")
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)

def read_block(kind,start,count):
    try:
        if kind=="input":
            rr=client.read_input_registers(address=start,count=count,device_id=1)
        else:
            rr=client.read_holding_registers(address=start,count=count,device_id=1)
        time.sleep(REQUEST_DELAY)
        stats["requests"]+=1
        if rr.isError():
            stats["failed"]+=1
            return None
        stats["success"]+=1
        return rr.registers
    except Exception:
        stats["requests"]+=1
        stats["failed"]+=1
        time.sleep(REQUEST_DELAY)
        return None

def read_single(kind,address):
    r=read_block(kind,address,1)
    if r is None:
        return False
    results[kind][address]=r[0]
    print(f"\n  ✓ {kind.upper()} {address} = {r[0]}")
    return True

for kind in ("input","holding"):
    print(f"\n=== Scanning {kind.upper()} registers ===")
    for start in range(10000,MAX_ADDRESS+1,BLOCK_SIZE):
        end=min(start+BLOCK_SIZE-1,MAX_ADDRESS)
        print(
            f"\r[{kind.upper():7}] {start:5}-{end:5} | "
            f"Req:{stats['requests']:6} "
            f"OK:{stats['success']:5} "
            f"Fail:{stats['failed']:5} "
            f"Found:{len(results[kind]):6}",
            end="",flush=True
        )
        regs=read_block(kind,start,end-start+1)
        if regs is not None:
            for i,v in enumerate(regs):
                results[kind][start+i]=v
            print(f"\n✓ Block {start}-{end}")
        else:
            for addr in range(start,end+1):
                read_single(kind,addr)
        if stats["success"] % SAVE_EVERY == 0 and stats["success"]>0:
            save()

shutdown()
