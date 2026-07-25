"""Values calculated from a decoded Modbus snapshot."""

from __future__ import annotations


PV_STRING_COUNT = 4


def add_derived_values(snapshot: dict[str, object]) -> dict[str, object]:
    """Return a snapshot augmented with calculated PV power values.

    The input is copied so the decoded Modbus snapshot remains a useful
    representation of only values read from the device.
    """
    result = snapshot.copy()
    pv_powers: list[float] = []

    for pv_index in range(1, PV_STRING_COUNT + 1):
        voltage = result.get(f"pv{pv_index}_voltage")
        current = result.get(f"pv{pv_index}_current")

        if isinstance(voltage, (int, float)) and isinstance(current, (int, float)):
            power = round(voltage * current, 2)
            result[f"pv{pv_index}_power"] = power
            pv_powers.append(power)

    if len(pv_powers) == PV_STRING_COUNT:
        result["pv_power_derived"] = round(sum(pv_powers), 2)

    return result
