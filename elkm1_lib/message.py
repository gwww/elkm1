"""
ElkM1 message encode/decode.

Message format:
    LLMM<data>00CC, where:
    LL - length in ASCII hex
    MM - message code
    <data> - message contents; length varies by message code
    00 - constant two characters reserved (almost all messages)
    CC - checksum

The panel numbers zones, keypads, etc. in base 1. The interface of
this module refers to them using base 0. Conversion to base 1 is done
on sending and conversion to base 0 is done on receiving. So, base 0/1
conversion is encapsulated in this module.
"""


from collections import namedtuple
import re

from .const import Max

MessageEncode = namedtuple('MessageEncode', ['message', 'response_command'])

_message_handlers = {}  # pylint: disable=invalid-name


def add_message_handler(message_type, handler):
    """Manage callbacks for message handlers."""
    if message_type not in _message_handlers:
        _message_handlers[message_type] = []

    handlers = _message_handlers[message_type]
    if handler not in handlers:
        handlers.append(handler)


def housecode_to_index(housecode):
    """Convert a X10 housecode to a zero-based index"""
    match = re.search(r'^([A-P])(\d{1,2})$', housecode.upper())
    if match:
        house_index = int(match.group(2))
        if 1 <= house_index <= 16:
            return (ord(match.group(1)) - ord('A')) * 16 + house_index - 1
    raise ValueError("Invalid X10 housecode: %s" % housecode)


def index_to_housecode(index):
    """Convert a zero-based index to a X10 housecode."""
    if index < 0 or index > 255:
        raise ValueError
    quotient, remainder = divmod(index, 16)
    return chr(quotient+ord('A')) + '{:02d}'.format(remainder+1)


def get_elk_command(line):
    """Return the 2 character command in the message."""
    if len(line) < 4:
        return ''
    return line[2:4]


def _status_decode(status):
    """Decode a 1 byte status into logical and physical statuses."""
    logical_status = (status & 0b00001100) >> 2
    physical_status = status & 0b00000011
    return (logical_status, physical_status)


class call_handlers():  # pylint: disable=invalid-name,too-few-public-methods
    """Decorator that calls out to message handlers"""
    def __init__(self, cmd):
        self.cmd = cmd

    def __call__(self, decode_func):
        def wrapped_f(msg):
            """Calls handlers"""
            decoded_msg = decode_func(msg)
            for handler in _message_handlers.get(self.cmd, []):
                handler(**decoded_msg)
        return wrapped_f


@call_handlers('AM')
def _am_decode(msg):
    """AM: Alarm memory by area report."""
    return {'alarm_memory': [x for x in msg[4:4+Max.AREAS.value]]}


@call_handlers('AS')
def _as_decode(msg):
    """AS: Arming status report."""
    return {'armed_statuses': [x for x in msg[4:12]],
            'arm_up_states': [x for x in msg[12:20]],
            'alarm_states': [x for x in msg[20:28]]}


@call_handlers('AZ')
def _az_decode(msg):
    """AZ: Alarm by zone report."""
    return {'alarm_status': [x for x in msg[4:4+Max.ZONES.value]]}


@call_handlers('CR')
def _cr_one_custom_value_decode(msg):
    index = int(msg[4:6])-1
    value = int(msg[6:11])
    value_format = int(msg[11])
    if value_format == 2:
        value = ((value >> 8) & 0xff, value & 0xff)
    return {'index': index, 'value': value, 'value_format': value_format}


def _cr_decode(msg):
    """CR: Custom values"""
    if int(msg[4:6]) > 0:
        _cr_one_custom_value_decode(msg)
    else:
        part = 6
        for i in range(Max.SETTINGS.value):
            newmsg = '0ECR{cv:02d}{val:s}'.format(cv=i+1, val=msg[part:part+6])
            _cr_one_custom_value_decode(newmsg)
            part += 6


@call_handlers('CC')
def _cc_decode(msg):
    """CC: Output status for single output."""
    return {'output': int(msg[4:7])-1, 'output_status': msg[7] == '1'}


@call_handlers('CS')
def _cs_decode(msg):
    """CS: Output status for all outputs."""
    output_status = [x == '1' for x in msg[4:4+Max.OUTPUTS.value]]
    return {'output_status': output_status}


@call_handlers('CV')
def _cv_decode(msg):
    """CV: Counter value."""
    return {'counter': int(msg[4:6])-1, 'value': int(msg[6:11])}


@call_handlers('EE')
def _ee_decode(msg):
    """EE: Entry/exit timer report."""
    return {'area': int(msg[4:5])-1, 'is_exit': msg[5:6] == '0',
            'timer1': int(msg[6:9]), 'timer2': int(msg[9:12]),
            'armed_status': msg[12:13]}


@call_handlers('IC')
def _ic_decode(msg):
    """IC: Send Valid Or Invalid User Code Format."""
    code = msg[4:16]
    if re.match(r'(0\d){6}', code):
        code = re.sub(r'0(\d)', r'\1', code)
    return {'code': code, 'user': int(msg[16:19])-1,
            'keypad': int(msg[19:21])-1}


@call_handlers('IE')
def _ie_decode(_msg):
    """IE: Installer mode exited."""
    return {}


@call_handlers('KA')
def _ka_decode(msg):
    """KA: Keypad areas for all keypads."""
    return {'keypad_areas': [ord(x)-0x31 for x in msg[4:4+Max.KEYPADS.value]]}


@call_handlers('KC')
def _kc_decode(msg):
    """KC: Keypad key change."""
    return {'keypad': int(msg[4:6])-1, 'key': int(msg[6:8])}


@call_handlers('LW')
def _lw_decode(msg):
    """LW: temperatures from all keypads and zones 1-16."""
    keypad_temps = []
    zone_temps = []
    for i in range(16):
        keypad_temps.append(int(msg[4+3*i:7+3*i]) - 40)
        zone_temps.append(int(msg[52+3*i:55+3*i]) - 60)
    return {'keypad_temps': keypad_temps, 'zone_temps': zone_temps}


@call_handlers('PC')
def _pc_decode(msg):
    """PC: PLC (lighting) change."""
    housecode = msg[4:7]
    return {'housecode': housecode, 'index': housecode_to_index(housecode),
            'light_level': int(msg[7:9])}


@call_handlers('PS')
def _ps_decode(msg):
    """PS: PLC (lighting) status."""
    return {'bank': ord(msg[4]) - 0x30,
            'statuses': [ord(x)-0x30 for x in msg[5:69]]}


@call_handlers('RP')
def _rp_decode(msg):
    """RP: Remote programming status."""
    return {'remote_programming_status': int(msg[4:6])}


@call_handlers('SD')
def _sd_decode(msg):
    """SD: Description text."""
    desc_ch1 = msg[9]
    show_on_keypad = ord(desc_ch1) >= 0x80
    if show_on_keypad:
        desc_ch1 = chr(ord(desc_ch1) & 0x7f)
    return {'desc_type': int(msg[4:6]), 'unit': int(msg[6:9])-1,
            'desc': (desc_ch1+msg[10:25]).rstrip(),
            'show_on_keypad': show_on_keypad}


@call_handlers('SS')
def _ss_decode(msg):
    """SS: System status."""
    return {'system_trouble_status': msg[4:-2]}


@call_handlers('ST')
def _st_decode(msg):
    """ST: Temperature update."""
    group = int(msg[4:5])
    temperature = int(msg[7:10])
    if group == 0:
        temperature -= 60
    elif group == 1:
        temperature -= 40
    return {'group': group, 'device': int(msg[5:7])-1,
            'temperature': temperature}


@call_handlers('TC')
def _tc_decode(msg):
    """TC: Task change."""
    return {'task': int(msg[4:7])-1}


@call_handlers('TR')
def _tr_decode(msg):
    """TR: Thermostat data response."""
    return {'thermostat_index': int(msg[4:6])-1, 'mode': int(msg[6]),
            'hold': msg[7] == '1', 'fan': int(msg[8]),
            'current_temp': int(msg[9:11]), 'heat_setpoint': int(msg[11:13]),
            'cool_setpoint': int(msg[13:15]), 'humidity': int(msg[15:17])}


@call_handlers('VN')
def _vn_decode(msg):
    """VN: Version information."""
    elkm1_version = "{}.{}.{}".format(int(msg[4:6], 16), int(msg[6:8], 16),
                                      int(msg[8:10], 16))
    xep_version = "{}.{}.{}".format(int(msg[10:12], 16), int(msg[12:14], 16),
                                    int(msg[14:16], 16))
    return {'elkm1_version': elkm1_version, 'xep_version': xep_version}


@call_handlers('XK')
def _xk_decode(msg):
    """XK: Ethernet Test."""
    return {'real_time_clock': msg[4:20]}


@call_handlers('ZB')
def _zb_decode(msg):
    """ZB: Zone bypass report."""
    return {'zone_number': int(msg[4:7])-1, 'zone_bypassed': msg[7] == '1'}


@call_handlers('ZC')
def _zc_decode(msg):
    """ZC: Zone Change."""
    status = _status_decode(int(msg[7:8], 16))
    return {'zone_number': int(msg[4:7])-1, 'zone_status': status}


@call_handlers('ZD')
def _zd_decode(msg):
    """ZD: Zone definitions."""
    zone_definitions = [ord(x)-0x30 for x in msg[4:4+Max.ZONES.value]]
    return {'zone_definitions': zone_definitions}


@call_handlers('ZP')
def _zp_decode(msg):
    """ZP: Zone partitions."""
    zone_partitions = [ord(x)-0x31 for x in msg[4:4+Max.ZONES.value]]
    return {'zone_partitions': zone_partitions}


@call_handlers('ZS')
def _zs_decode(msg):
    """ZS: Zone statuses."""
    status = [_status_decode(int(x, 16)) for x in msg[4:4+Max.ZONES.value]]
    return {'zone_statuses': status}


@call_handlers('ZV')
def _zv_decode(msg):
    """ZV: Zone voltage."""
    return {'zone_number': int(msg[4:7])-1, 'zone_voltage': int(msg[7:10])/10}


@call_handlers('unknown')
def _unknown_decode(msg):
    """Generic handler called when no specific handler exists"""
    return {'msg_code': msg[2:4], 'data': msg[4:-2]}


@call_handlers('timeout')
def timeout_decode(msg_code):
    """Called directly when a timeout happens when response not received"""
    return {'msg_code': msg_code}


def _check_checksum(msg):
    """Ensure checksum in message is good."""
    checksum = int(msg[-2:], 16)
    for char in msg[:-2]:
        checksum += ord(char)
    if (checksum % 256) != 0:
        raise ValueError("Elk message checksum invalid")


def _check_message_valid(msg):
    """Check packet length valid and that checksum is good."""
    try:
        if int(msg[:2], 16) != (len(msg) - 2):
            raise ValueError("Elk message length incorrect")
        _check_checksum(msg)
    except IndexError:
        raise ValueError("Elk message length incorrect")


def message_decode(msg):
    """Decode an Elk message by passing to appropriate decoder"""
    _check_message_valid(msg)

    cmd = msg[2:4]
    if not cmd.isupper():
        raise ValueError("Invalid message code")

    decoder_name = '_' + cmd.lower() + '_decode'
    try:
        if not callable(globals()[decoder_name]):
            raise ValueError
    except (KeyError, ValueError):
        _unknown_decode(msg)
        return
    globals()[decoder_name](msg)


def al_encode(arm_mode, area, user_code):
    """al: Arm system. Note in 'al' the 'l' can vary"""
    return MessageEncode('0Da{}{:1d}{:06d}00'.format(arm_mode, area+1,
                                                     user_code), 'AS')


def as_encode():
    """as: Get area status."""
    return MessageEncode('06as00', 'AS')


def az_encode():
    """az: Get alarm by zone."""
    return MessageEncode('06az00', 'AZ')


def cf_encode(output):
    """cf: Turn off output."""
    return MessageEncode('09cf{:03d}00'.format(output+1), None)


def ct_encode(output):
    """ct: Toggle output."""
    return MessageEncode('09ct{:03d}00'.format(output+1), None)


def cn_encode(output, time):
    """cn: Turn on output."""
    return MessageEncode('0Ecn{:03d}{:05d}00'.format(output+1, time), None)


def cs_encode():
    """cs: Get all output status."""
    return MessageEncode('06cs00', 'CS')


def cp_encode():
    """cp: Get ALL custom values."""
    return MessageEncode('06cp00', 'CR')


def cr_encode(index):
    """cr: Get a custom value."""
    return MessageEncode('08cr{cv:02d}00'.format(cv=index+1), 'CR')


def cw_encode(index, value, value_format):
    """cw: Write a custom value."""
    if value_format == 2:
        value = value[0] << 8 + value[1]
    return MessageEncode('0Dcw{:02d}{:05d}00'.format(index+1, value), None)


def cv_encode(counter):
    """cv: Get counter."""
    return MessageEncode('08cv{c:02d}00'.format(c=counter+1), 'CV')


def cx_encode(counter, value):
    """cx: Change counter value."""
    return MessageEncode('0Dcx{:02d}{:05d}00'.format(counter+1, value), 'CV')


# pylint: disable=too-many-arguments
def dm_encode(keypad_area, clear, beep, timeout, line1, line2):
    """dm: Display message on keypad."""
    return MessageEncode(
        '2Edm{:1d}{:1d}{:1d}{:05d}{:^<16.16}{:^<16.16}00'
        .format(keypad_area+1, clear, beep, timeout, line1, line2), None
    )


def ka_encode():
    """ka: Get keypad areas."""
    return MessageEncode('06ka00', 'KA')


def lw_encode():
    """lw: Get temperature data."""
    return MessageEncode('06lw00', 'LW')


def pc_encode(index, function_code, extended_code, time):
    """pc: Control any PLC device."""
    return MessageEncode('11pc{hc}{fc:02d}{ec:02d}{time:04d}00'.
                         format(hc=index_to_housecode(index),
                                fc=function_code, ec=extended_code,
                                time=time), None)


def pf_encode(index):
    """pf: Turn off light."""
    return MessageEncode('09pf{}00'.format(index_to_housecode(index)), None)


def pn_encode(index):
    """pn: Turn on light."""
    return MessageEncode('09pn{}00'.format(index_to_housecode(index)), None)


def ps_encode(bank):
    """ps: Get lighting status."""
    return MessageEncode('07ps{:1d}00'.format(bank), 'PS')


def pt_encode(index):
    """pt: Toggle light."""
    return MessageEncode('09pt{}00'.format(index_to_housecode(index)), None)


def sd_encode(desc_type, unit):
    """sd: Get description."""
    return MessageEncode('0Bsd{:02d}{:03d}00'.format(desc_type, unit+1), 'SD')


def sp_encode(phrase):
    """sp: Speak phrase."""
    return MessageEncode('09sp{:03d}00'.format(phrase), None)


def ss_encode():
    """ss: Get system trouble status."""
    return MessageEncode('06ss00', 'SS')


def sw_encode(word):
    """sp: Speak word."""
    return MessageEncode('09sw{:03d}00'.format(word), None)


def tn_encode(task):
    """tn: Activate task."""
    return MessageEncode('09tn{:03d}00'.format(task+1), None)


def tr_encode(thermostat):
    """tr: Request thermostat data."""
    return MessageEncode('08tr{:02d}00'.format(thermostat+1), None)


def ts_encode(thermostat, value, element):
    """ts: Set thermostat data."""
    return MessageEncode('0Bts{:02d}{:02d}{:1d}00'.format(
        thermostat+1, value, element), None)


def vn_encode():
    """zd: Get panel software version information."""
    return MessageEncode('06vn00', 'VN')


def zb_encode(zone, area, user_code):
    """zb: Zone bypass. Zone < 0 unbypass all; Zone > Max bypass all."""
    if zone < 0:
        zone = 0
    elif zone > Max.ZONES.value:
        zone = 999
    else:
        zone += 1
    return MessageEncode('10zb{zone:03d}{area:1d}{code:06d}00'.format(
        zone=zone, area=area+1, code=user_code), 'ZB')


def zd_encode():
    """zd: Get zone definitions"""
    return MessageEncode('06zd00', 'ZD')


def zp_encode():
    """zp: Get zone partitions"""
    return MessageEncode('06zp00', 'ZP')


def zs_encode():
    """zs: Get zone statuses"""
    return MessageEncode('06zs00', 'ZS')


def zt_encode(zone):
    """zt: Trigger zone."""
    return MessageEncode('09zt{zone:03d}00'.format(zone=zone+1), None)


def zv_encode(zone):
    """zv: Get zone voltage"""
    return MessageEncode('09zv{zone:03d}00'.format(zone=zone+1), 'ZV')
