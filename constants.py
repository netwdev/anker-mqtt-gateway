from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    key: str
    register_type: str
    address: int
    count: int
    scale: int = 1


REGISTER_RANGES = [
    # Keep each request within Modbus's 125-register limit while covering
    # only the addresses used by FIELD_SPECS below.
    ("input", 10000, 10124),
    ("input", 10156, 10265),
    ("input", 32768, 32774),
    ("input", 60000, 60003),

    ("holding", 10000, 10124),
    ("holding", 10156, 10265),
    ("holding", 32768, 32774),
    ("holding", 60000, 60003),
]


FIELD_SPECS = [
    # Device
    FieldSpec("device_model", "STRING", 32768, 5),
    #FieldSpec("device_model_2", "STRING", 10090, 3),
    FieldSpec("device_sn", "STRING", 10100, 12),
    FieldSpec("device_sw_version", "STRING", 10112, 6),
    #FieldSpec("device_sw_version_LE", "STRING_LE", 10118, 5),
    FieldSpec("system_time", "UINT32", 10060, 2),

    # Status
    FieldSpec("battery_status", "UINT16", 10001, 1),
    FieldSpec("ems_mode_mask", "UINT16", 32774, 1),

    # Battery
    FieldSpec("battery_soc", "UINT16", 10014, 1),
    #FieldSpec("battery_soc_2", "UINT16", 10256, 1),
    FieldSpec("battery_soh", "UINT16", 10015, 1),
    FieldSpec("battery_power", "INT32", 10008, 2),
    FieldSpec("battery_power_real", "INT32", 10254, 2),

    FieldSpec("rated_energy", "UINT32", 10250, 2, 10),
    FieldSpec("max_charge_power", "INT32", 10036, 2),
    FieldSpec("max_discharge_power", "INT32", 10038, 2),

    # Current power
    FieldSpec("pv_power", "INT32", 10002, 2),
    FieldSpec("third_party_pv_power", "INT32", 10004, 2),
    FieldSpec("load_power", "INT32", 10010, 2),
    FieldSpec("grid_power", "INT32", 10012, 2),
    FieldSpec("ac_grid_output_power", "INT32", 10208, 2),

    # Energy counters
    FieldSpec("pv_total_generation", "UINT32", 10018, 2, 10),
    FieldSpec("battery_charge_total", "UINT32", 10022, 2, 10),
    FieldSpec("load_total", "UINT32", 10026, 2, 10),
    FieldSpec("grid_export_total", "UINT32", 10030, 2, 10),
    FieldSpec("ac_grid_energy_total", "UINT32", 10034, 2, 10),
    FieldSpec("charge_energy_total", "UINT32", 10262, 2, 10),
    FieldSpec("discharge_energy_total", "UINT32", 10264, 2, 10),

    # Temperature
    FieldSpec("internal_temperature", "INT16", 10156, 1, 10),

    # PV strings
    FieldSpec("pv1_voltage", "INT16", 10167, 1, 10),
    FieldSpec("pv1_current", "INT16", 10168, 1, 100),
    FieldSpec("pv2_voltage", "INT16", 10169, 1, 10),
    FieldSpec("pv2_current", "INT16", 10170, 1, 100),
    FieldSpec("pv3_voltage", "INT16", 10171, 1, 10),
    FieldSpec("pv3_current", "INT16", 10172, 1, 100),
    FieldSpec("pv4_voltage", "INT16", 10173, 1, 10),
    FieldSpec("pv4_current", "INT16", 10174, 1, 100),

    # Grid
    FieldSpec("grid_voltage", "UINT16", 10199, 1, 10),
    FieldSpec("phase_a_voltage", "UINT16", 10202, 1, 10),
    FieldSpec("grid_current", "UINT16", 10205, 1, 100),
    FieldSpec("grid_frequency", "UINT16", 10213, 1, 100),
    FieldSpec("backup_grid_frequency", "UINT16", 10238, 1, 100),
]

# mqtt -> modbus mapping for publishing points
PUBLISH_POINTS = [
    # Device
    ("device/model", "device_model"),
    #("device/model_alt", "device_model_2"),
    ("device/sn", "device_sn"),
    ("device/sw_version", "device_sw_version"),
    #("device/sw_version_le", "device_sw_version_LE"),
    ("device/system_time", "system_time"),

    # Status
    ("status/battery_status", "battery_status"),
    ("status/ems_mode_mask", "ems_mode_mask"),

    # Battery
    ("battery/curr/battery_soc", "battery_soc"),
    #("battery/curr/battery_soc_2", "battery_soc_2"),
    ("battery/curr/battery_soh", "battery_soh"),
    ("battery/curr/battery_power", "battery_power"),
    ("battery/curr/battery_power_real", "battery_power_real"),
    ("battery/cfg/rated_energy", "rated_energy"),
    ("battery/cfg/max_charge_power", "max_charge_power"),
    ("battery/cfg/max_discharge_power", "max_discharge_power"),

    # Power (current)
    ("power/curr/pv_power", "pv_power"),
    ("power/curr/pv_power_derived", "pv_power_derived"),
    ("power/curr/third_party_pv_power", "third_party_pv_power"),
    ("power/curr/load_power", "load_power"),
    ("power/curr/grid_power", "grid_power"),
    ("power/curr/ac_grid_output_power", "ac_grid_output_power"),

    # Power (totals)
    ("power/cnt/pv_total_generation", "pv_total_generation"),
    ("power/cnt/load_total", "load_total"),
    ("power/cnt/grid_export_total", "grid_export_total"),
    ("power/cnt/ac_grid_energy_total", "ac_grid_energy_total"),
    ("power/cnt/battery_charge_total", "battery_charge_total"),
    ("power/cnt/charge_energy_total", "charge_energy_total"),
    ("power/cnt/discharge_energy_total", "discharge_energy_total"),

    # PV strings
    ("pv/1/voltage", "pv1_voltage"),
    ("pv/1/current", "pv1_current"),
    ("pv/1/power", "pv1_power"),
    ("pv/2/voltage", "pv2_voltage"),
    ("pv/2/current", "pv2_current"),
    ("pv/2/power", "pv2_power"),
    ("pv/3/voltage", "pv3_voltage"),
    ("pv/3/current", "pv3_current"),
    ("pv/3/power", "pv3_power"),
    ("pv/4/voltage", "pv4_voltage"),
    ("pv/4/current", "pv4_current"),
    ("pv/4/power", "pv4_power"),

    # Grid
    ("grid/voltage", "grid_voltage"),
    ("grid/current", "grid_current"),
    ("grid/frequency", "grid_frequency"),
    ("grid/backup_frequency", "backup_grid_frequency"),
    ("grid/phase_a_voltage", "phase_a_voltage"),

    # Temperature
    ("temperature/internal", "internal_temperature"),
]
