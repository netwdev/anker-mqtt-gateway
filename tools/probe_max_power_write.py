"""
Probe writing max_charge_power / max_discharge_power on the Anker SOLIX.

Tries int32 (10036/10038) and int16 (10037/10039) encodings, with and without
a -1 address offset. Reads always start at 10000 — single-register reads of
the target addresses fail on this device.
"""

from __future__ import annotations

import argparse
import os
import time

from dotenv import load_dotenv
from pymodbus.client import ModbusTcpClient

load_dotenv()

HOST = os.getenv("MODBUS_HOST", "192.168.1.100")
PORT = int(os.getenv("MODBUS_PORT", "502"))
UNIT_ID = 1

READ_START = 10000
READ_COUNT = 50  # covers 10000..10049

TARGETS = {
    "max_charge_power": {"int32_addr": 10036, "int16_addr": 10037},
    "max_discharge_power": {"int32_addr": 10038, "int16_addr": 10039},
}


def s16(raw: int) -> int:
    return raw - 0x10000 if raw >= 0x8000 else raw


def s32_be(hi: int, lo: int) -> int:
    value = (hi << 16) | lo
    return value - 0x100000000 if value >= 0x80000000 else value


def to_u16(value: int) -> int:
    return value & 0xFFFF


def to_u32_words(value: int) -> list[int]:
    raw = value & 0xFFFFFFFF
    return [(raw >> 16) & 0xFFFF, raw & 0xFFFF]


def read_block(client: ModbusTcpClient) -> dict[int, int] | None:
    rr = client.read_holding_registers(
        address=READ_START,
        count=READ_COUNT,
        device_id=UNIT_ID,
    )
    if rr.isError():
        print(f"  READ ERROR from {READ_START}: {rr}")
        return None
    return {READ_START + i: v for i, v in enumerate(rr.registers)}


def snapshot_values(regs: dict[int, int]) -> dict[str, object]:
    return {
        "u16@10036": regs.get(10036),
        "u16@10037": regs.get(10037),
        "u16@10038": regs.get(10038),
        "u16@10039": regs.get(10039),
        "s16@10037": s16(regs[10037]) if 10037 in regs else None,
        "s16@10039": s16(regs[10039]) if 10039 in regs else None,
        "s32@10036": (
            s32_be(regs[10036], regs[10037]) if 10036 in regs and 10037 in regs else None
        ),
        "s32@10038": (
            s32_be(regs[10038], regs[10039]) if 10038 in regs and 10039 in regs else None
        ),
    }


def fmt_snapshot(snap: dict[str, object]) -> str:
    return (
        f"int32 charge={snap['s32@10036']} discharge={snap['s32@10038']} | "
        f"int16 charge={snap['s16@10037']} discharge={snap['s16@10039']} | "
        f"raw [10036..10039]="
        f"{snap['u16@10036']},{snap['u16@10037']},{snap['u16@10038']},{snap['u16@10039']}"
    )


def changed(before: dict[str, object], after: dict[str, object]) -> bool:
    keys = ("u16@10036", "u16@10037", "u16@10038", "u16@10039")
    return any(before.get(k) != after.get(k) for k in keys)


def try_write(
    client: ModbusTcpClient,
    label: str,
    address: int,
    values: list[int],
) -> tuple[bool, str]:
    if len(values) == 1:
        result = client.write_register(
            address=address,
            value=values[0],
            device_id=UNIT_ID,
        )
    else:
        result = client.write_registers(
            address=address,
            values=values,
            device_id=UNIT_ID,
        )

    if result.isError():
        return False, f"WRITE ERROR ({label} addr={address} values={values}): {result}"
    return True, f"WRITE OK   ({label} addr={address} values={values})"


def restore_with_same_method(
    client: ModbusTcpClient,
    regs_before: dict[int, int],
    address: int,
    values: list[int],
    settle_s: float,
) -> None:
    """Restore using the same address/width that just succeeded."""
    # Build original payload from the logical device registers that were touched.
    # For addr-1 attempts, the physical write hit address, but values live at address+1.
    candidates = [
        address,
        address + 1,  # if we used -1 offset against the real register
    ]
    for start in candidates:
        words = []
        ok = True
        for i in range(len(values)):
            a = start + i
            if a not in regs_before:
                ok = False
                break
            words.append(regs_before[a])
        if not ok:
            continue
        try_write(client, "restore", address, words)
        time.sleep(settle_s)
        return


def build_attempts(name: str, new_value: int) -> list[tuple[str, int, list[int]]]:
    addrs = TARGETS[name]
    int32_addr = addrs["int32_addr"]
    int16_addr = addrs["int16_addr"]
    words = to_u32_words(new_value)
    word16 = [to_u16(new_value)]

    return [
        (f"{name} int16 direct", int16_addr, word16),
        (f"{name} int16 addr-1", int16_addr - 1, word16),
        (f"{name} int32BE direct", int32_addr, words),
        (f"{name} int32BE addr-1", int32_addr - 1, words),
        (f"{name} int32LE direct", int32_addr, list(reversed(words))),
        (f"{name} int32LE addr-1", int32_addr - 1, list(reversed(words))),
        (f"{name} int32BE @int16", int16_addr, words),
        (f"{name} int32BE @int16-1", int16_addr - 1, words),
    ]


def run_probe(target: str, new_value: int, settle_s: float) -> None:
    client = ModbusTcpClient(HOST, port=PORT, timeout=5)
    if not client.connect():
        raise RuntimeError(f"Could not connect to {HOST}:{PORT}")

    print(f"Connected to {HOST}:{PORT}")
    print(f"Target={target}  new_value={new_value}\n")

    before_regs = read_block(client)
    if before_regs is None:
        client.close()
        return

    before = snapshot_values(before_regs)
    print(f"BEFORE: {fmt_snapshot(before)}\n")

    successes: list[str] = []

    for label, address, values in build_attempts(target, new_value):
        print(f"-- trying: {label}")
        ok, msg = try_write(client, label, address, values)
        print(f"  {msg}")
        if not ok:
            print()
            continue

        time.sleep(settle_s)
        after_regs = read_block(client)
        if after_regs is None:
            print()
            continue

        after = snapshot_values(after_regs)
        did_change = changed(before, after)
        print(f"  AFTER:  {fmt_snapshot(after)}")

        if did_change:
            print("  >>> VALUE CHANGED — candidate looks writable")
            successes.append(label)
            restore_with_same_method(client, before_regs, address, values, settle_s)
            restored = read_block(client)
            if restored:
                before_regs = restored
                before = snapshot_values(restored)
                print(f"  restored baseline: {fmt_snapshot(before)}")
        else:
            print("  (write accepted but registers unchanged)")
        print()

    client.close()

    print("=" * 60)
    if successes:
        print("Successful write+change candidates:")
        for s in successes:
            print(f"  - {s}")
    else:
        print(
            "No attempt both succeeded without Modbus error AND changed the registers."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=["max_charge_power", "max_discharge_power", "both"],
        default="both",
        help="Which limit to probe (default: both)",
    )
    parser.add_argument(
        "--value",
        type=int,
        default=800,
        help="Value to write in watts (default: 800)",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=0.5,
        help="Seconds to wait after write before re-read (default: 0.5)",
    )
    args = parser.parse_args()

    targets = (
        ["max_charge_power", "max_discharge_power"]
        if args.target == "both"
        else [args.target]
    )
    for t in targets:
        run_probe(t, args.value, args.settle)
        print()


if __name__ == "__main__":
    main()
