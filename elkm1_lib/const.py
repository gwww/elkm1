"""
Constants used across package
"""

from enum import Enum
from typing import NamedTuple


class Max(Enum):
    """Max number of elements on the panel"""

    AREAS = 8
    COUNTERS = 64
    KEYPADS = 16
    OUTPUTS = 208
    SETTINGS = 20
    TASKS = 32
    THERMOSTATS = 16
    USERS = 203
    LIGHTS = 256
    ZONES = 208
    ZONE_TEMPS = 16


class ZoneType(Enum):
    """Types of Elk zones"""

    DISABLED = 0
    BURGLAR_ENTRY_EXIT_1 = 1
    BURGLAR_ENTRY_EXIT_2 = 2
    BURGLAR_PERIMETER_INSTANT = 3
    BURGLAR_INTERIOR = 4
    BURGLAR_INTERIOR_FOLLOWER = 5
    BURGLAR_INTERIOR_NIGHT = 6
    BURGLAR_INTERIOR_NIGHT_DELAY = 7
    BURGLAR24_HOUR = 8
    BURGLAR_BOX_TAMPER = 9
    FIRE_ALARM = 10
    FIRE_VERIFIED = 11
    FIRE_SUPERVISORY = 12
    AUX_ALARM_1 = 13
    AUX_ALARM_2 = 14
    KEYFOB = 15
    NON_ALARM = 16
    CARBON_MONOXIDE = 17
    EMERGENCY_ALARM = 18
    FREEZE_ALARM = 19
    GAS_ALARM = 20
    HEAT_ALARM = 21
    MEDICAL_ALARM = 22
    POLICE_ALARM = 23
    POLICE_NO_INDICATION = 24
    WATER_ALARM = 25
    KEY_MOMENTARY_ARM_DISARM = 26
    KEY_MOMENTARY_ARM_AWAY = 27
    KEY_MOMENTARY_ARM_STAY = 28
    KEY_MOMENTARY_DISARM = 29
    KEY_ON_OFF = 30
    MUTE_AUDIBLES = 31
    POWER_SUPERVISORY = 32
    TEMPERATURE = 33
    ANALOG_ZONE = 34
    PHONE_KEY = 35
    INTERCOM_KEY = 36


class ZonePhysicalStatus(Enum):
    """Zone physical status."""

    UNCONFIGURED = 0
    OPEN = 1
    EOL = 2
    SHORT = 3


class ZoneLogicalStatus(Enum):
    """Zone logical status."""

    NORMAL = 0
    TROUBLED = 1
    VIOLATED = 2
    BYPASSED = 3


class ArmedStatus(Enum):
    """Area arming status: armed status"""

    DISARMED = "0"
    ARMED_AWAY = "1"
    ARMED_STAY = "2"
    ARMED_STAY_INSTANT = "3"
    ARMED_TO_NIGHT = "4"
    ARMED_TO_NIGHT_INSTANT = "5"
    ARMED_TO_VACATION = "6"


class ArmUpState(Enum):
    """Area arming status: Ability to arm"""

    NOT_READY_TO_ARM = "0"
    READY_TO_ARM = "1"
    CAN_BE_FORCE_ARMED = "2"
    ARMED_AND_EXIT_TIMER_RUNNING = "3"
    FULLY_ARMED = "4"
    FORCE_ARMED = "5"
    ARMED_WITH_BYPASS = "6"


class AlarmState(Enum):
    """Area arming status: Current alarm state"""

    NO_ALARM_ACTIVE = "0"
    ENTRANCE_DELAY_ACTIVE = "1"
    ALARM_ABORT_DELAY_ACTIVE = "2"
    FIRE_ALARM = "3"
    MEDICAL_ALARM = "4"
    POLICE_ALARM = "5"
    BURGLAR_ALARM = "6"
    AUX_1_ALARM = "7"
    AUX_2_ALARM = "8"
    AUX_3_ALARM = "9"
    AUX_4_ALARM = ":"
    CARBON_MONOXIDE_ALARM = ";"
    EMERGENCY_ALARM = "<"
    FREEZE_ALARM = "="
    GAS_ALARM = ">"
    HEAT_ALARM = "?"
    WATER_ALARM = "@"
    FIRE_SUPERVISORY = "A"
    VERIFY_FIRE = "B"
    UNSUPERVISED_ZONE_TROUBLE = "U"


class ArmLevel(Enum):
    """Levels for Arm/Disarm al_encode messages"""

    DISARM = "0"
    ARMED_AWAY = "1"
    ARMED_STAY = "2"
    ARMED_STAY_INSTANT = "3"
    ARMED_NIGHT = "4"
    ARMED_NIGHT_INSTANT = "5"
    ARMED_VACATION = "6"
    ARM_TO_NEXT_AWAY_MODE = "7"
    ARM_TO_NEXT_STAY_MODE = "8"
    FORCE_ARM_TO_AWAY_MODE = "9"
    FORCE_ARM_TO_STAY_MODE = ":"


class ZoneAlarmState(Enum):
    """Alarm state for a zone"""

    NO_ALARM = "0"
    BURGLAR_ENTRY_EXIT_1 = "1"
    BURGLAR_ENTRY_EXIT_2 = "2"
    BURGLAR_PERIMETER_INSTANT = "3"
    BURGLAR_INTERIOR = "4"
    BURGLAR_INTERIOR_FOLLOWER = "5"
    BURGLAR_INTERIOR_NIGHT = "6"
    BURGLAR_INTERIOR_NIGHT_DELAY = "7"
    BURGLAR_24_HOUR = "8"
    BURGLAR_BOX_TAMPER = "9"
    FIRE_ALARM = ":"
    FIRE_VERIFIED = ";"
    FIRE_SUPERVISORY = "<"
    AUX_ALARM_1 = "="
    AUX_ALARM_2 = ">"
    KEYFOB = "?"  # not used
    NON_ALARM = "@"  # not used
    CARBON_MONOXIDE = "A"
    EMERGENCY_ALARM = "B"
    FREEZE_ALARM = "C"
    GAS_ALARM = "D"
    HEAT_ALARM = "E"
    MEDICAL_ALARM = "F"
    POLICE_ALARM = "G"
    POLICE_NO_INDICATION = "H"
    WATER_ALARM = "I"


class KeypadKeys(Enum):
    """Keys on the keypad."""

    NO_KEY = 0
    USER_CODE_ENTERED = 0
    STAR = 11
    POUND = 12
    F1 = 13
    F2 = 14
    F3 = 15
    F4 = 16
    STAY = 17
    EXIT = 18
    CHIME = 19
    BYPASS = 20
    ELK = 21
    DOWN = 22
    UP = 23
    RIGHT = 24
    LEFT = 25
    F6 = 26
    F5 = 27
    DATA_KEY_MODE = 28


class FunctionKeys(Enum):
    """From KF: Which function key pressed"""

    FORCE_KF_SYNC = "0"
    F1 = "1"
    F2 = "2"
    F3 = "3"
    F4 = "4"
    F5 = "5"
    F6 = "6"
    STAR = "*"
    CHIME = "C"


class ChimeMode(Enum):
    """Chime mode settings on an Area"""

    OFF = 0
    CHIME = 1
    VOICE = 2
    CHIMEANDVOICE = 3


class TextDescription(NamedTuple):
    """A text description."""

    desc_type: int
    number_descriptions: int


class TextDescriptions(Enum):
    """Types of description strings that can be retrieved from the panel"""

    ZONE = TextDescription(0, Max.ZONES.value)
    AREA = TextDescription(1, Max.AREAS.value)
    USER = TextDescription(2, Max.USERS.value)
    KEYPAD = TextDescription(3, Max.KEYPADS.value)
    OUTPUT = TextDescription(4, 64)
    TASK = TextDescription(5, Max.TASKS.value)
    TELEPHONE = TextDescription(6, 0)
    LIGHT = TextDescription(7, Max.LIGHTS.value)
    ALARM_DURATION = TextDescription(8, 0)
    SETTING = TextDescription(9, Max.SETTINGS.value)
    COUNTER = TextDescription(10, Max.COUNTERS.value)
    THERMOSTAT = TextDescription(11, Max.THERMOSTATS.value)
    FUNCTION_KEY_1 = TextDescription(12, 0)
    FUNCTION_KEY_2 = TextDescription(13, 0)
    FUNCTION_KEY_3 = TextDescription(14, 0)
    FUNCTION_KEY_4 = TextDescription(15, 0)
    FUNCTION_KEY_5 = TextDescription(16, 0)
    FUNCTION_KEY_6 = TextDescription(17, 0)
    AUDIO_ZONE = TextDescription(18, 0)
    AUDIO_SOURCE = TextDescription(19, 0)


# Map to convert message code to descriptive string
MESSAGE_MAP = {
    "AM": "Alarm memory update",
    "AP": "Send ASCII String",
    "AR": "Alarm Reporting to Ethernet",
    "AS": "Arming status report data",
    "AT": "Ethernet Test to IP",
    "AZ": "Alarm by zone reply",
    "CA": "Reply Touchscreen audio command",
    "CC": "Control output change update",
    "CD": "Outgoing Audio Equip Command",
    "CR": "Custom value report data",
    "CS": "Control output status report data",
    "CU": "Change user code reply",
    "CV": "Counter Value Data",
    "DK": "Display KP LCD Data, not used",
    "DS": "Lighting Poll Response",
    "EE": "Entry/Exit Time Data",
    "EM": "Email Trigger to M1XEP",
    "IC": "Send invalid user code digits",
    "IE": "Installer program exited",
    "IP": "M1XSP Insteon Program",
    "IR": "M1XSP Insteon Read",
    "KA": "Keypad areas report data",
    "KC": "Keypad key change update",
    "KF": "Function key pressed data",
    "LD": "Log data with index",
    "LW": "Reply temperature data",
    "NS": "Reply Source Name",
    "NZ": "Reply Zone Name",
    "PC": "PLC change update",
    "PS": "PLC status report data",
    "RE": "Reset Ethernet Module",
    "RP": "ELKRP connected",
    "RR": "Real Time Clock Data",
    "SD": "Text string description report data",
    "SS": "System Trouble Status data",
    "ST": "Temperature report data",
    "T2": "Reply Omnistat 2 data",
    "TC": "Task change update",
    "TR": "Thermostat data report",
    "UA": "User code areas report data",
    "VN": "Reply Version Number of M1",
    "XB": "reserved by ELKRP",
    "XK": "Request Ethernet test",
    "ZB": "Zone bypass report data",
    "ZC": "Zone change update",
    "ZD": "Zone definition report data",
    "ZP": "Zone partition report data",
    "ZS": "Zone status report data",
    "ZV": "Zone analog voltage data",
    "a0": "Disarm",
    "a1": "Arm to away",
    "a2": "Arm to stay",
    "a3": "Arm to stay instant",
    "a4": "Arm to night",
    "a5": "Arm to night instant",
    "a6": "Arm to vacation",
    "a7": "Arm, step to next Away Mode",
    "a8": "Arm, step to next Stay Mode",
    "a9": "Force Arm to Away Mode",
    "a:": "Force Arm to Stay Mode",
    "ar": "Alarm Reporting Acknowledge",
    "as": "Request arming status",
    "at": "Ethernet Test Acknowledge",
    "az": "Alarm by zone request",
    "ca": "Request Touchscreen audio command",
    "cd": "Incoming Audio Equip Command",
    "cf": "Control output OFF",
    "cn": "Control output ON",
    "cp": "Request ALL custom values",
    "cr": "Request custom value",
    "cs": "Control output status request",
    "ct": "Control output TOGGLE",
    "cu": "Change user code request",
    "cv": "Request Counter value",
    "cw": "Write custom value data",
    "cx": "Write counter value",
    "dm": "Display message",
    "ds": "Lighting Poll Request",
    "ip": "M1XSP Insteon Program",
    "ir": "M1XSP Insteon Read",
    "ka": "Request keypad areas",
    "kc": "Request F Key illumination status",
    "kf": "Request simulated function key press",
    "ld": "Request log data, with index",
    "le": "Write Log Data Entry",
    "lw": "Request temperature data",
    "pc": "Control any PLC device",
    "pf": "Turn OFF PLC device",
    "pn": "Turn ON PLC device",
    "ps": "Request PLC status",
    "pt": "Toggle PLC device",
    "rr": "Request Real Time Clock Read",
    "rs": "Used by Touchscreen",
    "rw": "Real Time Clock Write",
    "sd": "Request text string descriptions",
    "sp": "Speak phrase",
    "ss": "Request System Trouble Status",
    "st": "Request temperature",
    "sw": "Speak word",
    "t2": "Request Omnistat 2 data",
    "tn": "Task activation",
    "tr": "Request thermostat data",
    "ts": "Set thermostat data",
    "ua": "Request user code areas",
    "vn": "request Version Number of M1",
    "xk": "Reply from Ethernet test",
    "zb": "Zone bypass request",
    "zd": "Request zone definition data",
    "zp": "Zone partition request",
    "zs": "Zone status request",
    "zv": "Request Zone analog voltage",
}


class ThermostatSetting(Enum):
    """Thermostat consts when setting"""

    MODE = 0
    HOLD = 1
    FAN = 2
    GET_TEMPERATURE = 3
    COOL_SETPOINT = 4
    HEAT_SETPOINT = 5


class ThermostatMode(Enum):
    """Thermostat modes"""

    OFF = 0
    HEAT = 1
    COOL = 2
    AUTO = 3
    EMERGENCY_HEAT = 4


class ThermostatFan(Enum):
    """Thermostat fan"""

    AUTO = 0
    ON = 1


class ThermostatHold(Enum):
    """Thermostat hold"""

    OFF = 0
    ON = 1


class SettingFormat(Enum):
    """Types of values for settings."""

    NUMBER = 0
    TIMER = 1
    TIME_OF_DAY = 2


class ElkRPStatus(Enum):
    """Elk remote programming status."""

    DISCONNECTED = 0
    CONNECTED = 1
    INITIALIZING = 2
