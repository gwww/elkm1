"""
Constants used across package
"""

from enum import Enum

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
    Disabled = 0
    BurlarEntryExit1 = 1
    BurlarEntryExit2 = 2
    BurglarPerimeterInstant = 3
    BurglarInterior = 4
    BurglarInteriorFollower = 5
    BurglarInteriorNight = 6
    BurglarInteriorNightDelay = 7
    Burglar24Hour = 8
    BurglarBoxTamper = 9
    FireAlarm = 10
    FireVerified = 11
    FireSupervisory = 12
    AuxAlarm1 = 13
    AuxAlarm2 = 14
    KeyFob = 15
    NonAlarm = 16
    CarbonMonoxide = 17
    EmergencyAlarm = 18
    FreezeAlarm = 19
    GasAlarm = 20
    HeatAlarm = 21
    MedicalAlarm = 22
    PoliceAlarm = 23
    PoliceNoIndication = 24
    WaterAlarm = 25
    KeyMomentaryArmDisarm = 26
    KeyMomentaryArmAway = 27
    KeyMomentaryArmStay = 28
    KeyMomentaryDisarm = 29
    KeyOnOff = 30
    MuteAudibles = 31
    PowerSupervisory = 32
    Temperature = 33
    AnalogZone = 34
    PhoneKey = 35
    IntercomKey = 36

class ZonePhysicalStatus(Enum):
    """Zone physical status; name capitalized so can be used in displays"""
    Unconfigured = 0
    Open = 1
    EOL = 2
    Short = 3

class ZoneLogicalStatus(Enum):
    """Zone logical status; name capitalized so can be used in displays"""
    Normal = 0
    Troubled = 1
    Violated = 2
    Bypassed = 3

class ArmedStatus(Enum):
    """Area arming status: armed status"""
    Disarmed = '0'
    ArmedAway = '1'
    ArmedStay = '2'
    ArmedStayInstant = '3'
    ArmedToNight = '4'
    ArmedToNightInstant  = '5'
    ArmedToVacation = '6'

class ArmUpState(Enum):
    """Area arming status: Ability to arm"""
    NotReadyToArm = '0'
    ReadyToArm = '1'
    CanBeForceArmed = '2'
    ArmedAndExitTimerRunning = '3'
    FullyArmed = '4'
    ForceArmed = '5'
    ArmedWithBypass = '6'

class AlarmState(Enum):
    """Area arming status: Current alarm state"""
    NoAlarmActive = '0'
    EntranceDelayActive = '1'
    AlarmAbortDelayActive = '2'
    FireAlarm = '3'
    MedicalAlarm = '4'
    PoliceAlarm = '5'
    BurlarAlarm = '6'
    Aux1Alarm = '7'
    Aux2Alarm = '8'
    Aux3Alarm = '9'
    Aux4Alarm = ':'
    CarbonMonoxideAlarm = ';'
    EmergencyAlarm = '<'
    FreezeAlarm= '='
    GasAlarm = '>'
    HeatAlarm = '?'
    WaterAlarm = '@'
    FireSupervisory = 'A'
    VerifyFire = 'B'

class ArmLevel(Enum):
    """Levels for Arm/Disarm al_encode messages"""
    Disarm = '0'
    ArmedAway = '1'
    ArmedStay = '2'
    ArmedStayInstant = '3'
    ArmedNight = '4'
    ArmedNightInstant = '5'
    ArmedVacation = '6'
    ArmToNextAwayMode  = '7'
    ArmToNextStayMode = '8'
    ForceArmToAwayMode  = '9'
    ForceArmToStayMode = ':'

class TextDescriptions(Enum):
    """Types of description strings that can be retrieved from the panel"""
    ZONE = (0, Max.ZONES.value)
    AREA = (1, Max.AREAS.value)
    USER = (2, Max.USERS.value)
    KEYPAD = (3, Max.KEYPADS.value)
    OUTPUT = (4, 64)
    TASK = (5, Max.TASKS.value)
    TELEPHONE = 6
    LIGHT = (7, Max.LIGHTS.value)
    ALARM_DURATION = 8
    SETTING = (9, Max.SETTINGS.value)
    COUNTER = (10, Max.COUNTERS.value)
    THERMOSTAT = (11, Max.THERMOSTATS.value)
    FUNCTION_KEY_1 = 12
    FUNCTION_KEY_2 = 13
    FUNCTION_KEY_3 = 14
    FUNCTION_KEY_4 = 15
    FUNCTION_KEY_5 = 16
    FUNCTION_KEY_6 = 17
    AUDIO_ZONE = 18
    AUDIO_SOURCE = 19

# Map to convert message code to descriptive string
MESSAGE_MAP = {
    'AP': "Send ASCII String",
    'AR': "Alarm Reporting to Ethernet",
    'AS': "Arming status report data",
    'AT': "Ethernet Test to IP",
    'AZ': "Alarm by zone reply",
    'CA': "Reply Touchscreen audio command",
    'CC': "Control output change update",
    'CD': "Outgoing Audio Equip Command",
    'CR': "Custom value report data",
    'CS': "Control output status report data",
    'CU': "Change user code reply",
    'CV': "Counter Value Data",
    'DK': "Display KP LCD Data, not used",
    'DS': "Lighting Poll Response",
    'EE': "Entry/Exit Time Data",
    'EM': "Email Trigger to M1XEP",
    'IC': "Send invalid user code digits",
    'IE': "Installer program exited",
    'IP': "M1XSP Insteon Program",
    'IR': "M1XSP Insteon Read",
    'KA': "Keypad areas report data",
    'KC': "Keypad key change update",
    'KF': "Function key pressed data",
    'LD': "Log data with index",
    'LW': "Reply temperature data",
    'NS': "Reply Source Name",
    'NZ': "Reply Zone Name",
    'PC': "PLC change update",
    'PS': "PLC status report data",
    'RE': "Reset Ethernet Module",
    'RP': "ELKRP connected",
    'RR': "Real Time Clock Data",
    'SD': "Text string description report data",
    'SS': "System Trouble Status data",
    'ST': "Temperature report data",
    'T2': "Reply Omnistat 2 data",
    'TC': "Task change update",
    'TR': "Thermostat data report",
    'UA': "User code areas report data",
    'VN': "Reply Version Number of M1",
    'XB': "reserved by ELKRP",
    'XK': "Request Ethernet test",
    'ZB': "Zone bypass report data",
    'ZC': "Zone change update",
    'ZD': "Zone definition report data",
    'ZP': "Zone partition report data",
    'ZS': "Zone status report data",
    'ZV': "Zone analog voltage data",

    'a0': "Disarm",
    'a1': "Arm to away",
    'a2': "Arm to stay",
    'a3': "Arm to stay instant",
    'a4': "Arm to night",
    'a5': "Arm to night instant",
    'a6': "Arm to vacation",
    'a7': "Arm, step to next Away Mode",
    'a8': "Arm, step to next Stay Mode",
    'a9': "Force Arm to Away Mode",
    'a:': "Force Arm to Stay Mode",
    'ar': "Alarm Reporting Acknowledge",
    'as': "Request arming status",
    'at': "Ethernet Test Acknowledge",
    'az': "Alarm by zone request",
    'ca': "Request Touchscreen audio command",
    'cd': "Incoming Audio Equip Command",
    'cf': "Control output OFF",
    'cn': "Control output ON",
    'cp': "Request ALL custom values",
    'cr': "Request custom value",
    'cs': "Control output status request",
    'ct': "Control output TOGGLE",
    'cu': "Change user code request",
    'cv': "Request Counter value",
    'cw': "Write custom value data",
    'cx': "Write counter value",
    'dm': "Display message",
    'ds': "Lighting Poll Request",
    'ip': "M1XSP Insteon Program",
    'ir': "M1XSP Insteon Read",
    'ka': "Request keypad areas",
    'kc': "Request F Key illumination status",
    'kf': "Request simulated function key press",
    'ld': "Request log data, with index",
    'le': "Write Log Data Entry",
    'lw': "Request temperature data",
    'pc': "Control any PLC device",
    'pf': "Turn OFF PLC device",
    'pn': "Turn ON PLC device",
    'ps': "Request PLC status",
    'pt': "Toggle PLC device",
    'rr': "Request Real Time Clock Read",
    'rs': "Used by Touchscreen",
    'rw': "Real Time Clock Write",
    'sd': "Request text string descriptions",
    'sp': "Speak phrase",
    'ss': "Request System Trouble Status",
    'st': "Request temperature",
    'sw': "Speak word",
    't2': "Request Omnistat 2 data",
    'tn': "Task activation",
    'tr': "Request thermostat data",
    'ts': "Set thermostat data",
    'ua': "Request user code areas",
    'vn': "request Version Number of M1",
    'xk': "Reply from Ethernet test",
    'zb': "Zone bypass request",
    'zd': "Request zone definition data",
    'zp': "Zone partition request",
    'zs': "Zone status request",
    'zv': "Request Zone analog voltage",
}

class ThermostatSetting(Enum):
    """Thermostat consts when setting"""
    ELEMENT_MODE = 0
    ELEMENT_HOLD = 1
    ELEMENT_FAN = 2
    ELEMENT_GET_TEMPERATURE = 3
    ELEMENT_COOL_SETPOINT = 4
    ELEMENT_HEAT_SETPOINT = 5

class ThermostatMode(Enum):
    """Thermostat modes"""
    MODE_OFF = 0
    MODE_HEAT = 1
    MODE_COOL = 2
    MODE_AUTO = 3
    MODE_EMERGENCY_HEAT = 4

class ThermostatFan(Enum):
    """Thermostat fan"""
    FAN_AUTO = 0
    FAN_ON = 1

class ThermostatHold(Enum):
    """Thermostat hold"""
    HOLD_OFF = 0
    HOLD_ON = 1
