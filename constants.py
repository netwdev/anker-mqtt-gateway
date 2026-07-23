from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    key: str
    register_type: str
    address: int
    count: int
    scale: int = 1


REGISTER_RANGES = [
    ("input", 10000, 10050),
    ("input", 10090, 10156),
    ("input", 10208, 10265),
    ("input", 32768, 32774),

    ("holding", 10060, 10072),
    ("holding", 10074, 10081),
    ("holding", 60000, 60003),
]


FIELD_SPECS = [
    FieldSpec("device_model", "STRING", 32768, 5),
    FieldSpec("device_sn", "STRING", 10100, 12),
    FieldSpec("device_sw_version", "STRING", 10112, 6),

    FieldSpec("battery_soc", "UINT16", 10014, 1),

    FieldSpec("pv_power", "INT32", 10002, 2),
    FieldSpec("load_power", "INT32", 10010, 2),
    FieldSpec("grid_import_power", "INT32", 10012, 2),
    FieldSpec("grid_export_power", "INT32", 10012, 2),

    FieldSpec("pv_total_generation", "UINT32", 10018, 2, 10),

    FieldSpec("cumulative_charge_energy", "UINT32", 10262, 2, 10),
    FieldSpec("cumulative_discharge_energy", "UINT32", 10264, 2, 10),

    FieldSpec("max_charge_power", "INT32", 10036, 2),
    FieldSpec("max_discharge_power", "INT32", 10038, 2),

    FieldSpec("battery_charging_power", "INT32", 10008, 2),
    FieldSpec("battery_discharging_power", "INT32", 10008, 2),

    FieldSpec("rated_energy", "UINT32", 10250, 2, 10),

    FieldSpec("battery_status", "UINT16", 10001, 1),
]

# mqtt -> modbus mapping for publishing points
PUBLISH_POINTS = [
    ("device/model", "device_model"),
    ("device/sn", "device_sn"),
    ("device/sw_version", "device_sw_version"),
    ("power/curr/pv_power", "pv_power"),
    ("power/curr/load_power", "load_power"),
    ("power/curr/grid_import_power", "grid_import_power"),
    ("power/curr/grid_export_power", "grid_export_power"),
    ("power/cnt/pv_total_generation", "pv_total_generation"),
    ("power/cnt/cumulative_charge_energy", "cumulative_charge_energy"),
    ("power/cnt/cumulative_discharge_energy", "cumulative_discharge_energy"),
    ("power/cfg/max_charge_power", "max_charge_power"),
    ("power/cfg/max_discharge_power", "max_discharge_power"),
    ("battery/curr/battery_soc", "battery_soc"),
    ("battery/curr/battery_charging_power", "battery_charging_power"),
    ("battery/curr/battery_discharging_power", "battery_discharging_power"),
    ("battery/cfg/rated_energy", "rated_energy"),
    ("status/battery_status", "battery_status"),
]