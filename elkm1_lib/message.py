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


class Message:
    """Message decode and dispatcher."""
    def __init__(self):
        """Initialize a new Message instance."""
        self._handlers = {}

    def add_handler(self, message_type, handler):
        """Manage callbacks for message handlers."""
        if message_type not in self._handlers:
            self._handlers[message_type] = []

        if handler not in self._handlers[message_type]:
            self._handlers[message_type].append(handler)

    def decode(self, msg):
        """Decode an Elk message by passing to appropriate decoder"""
        _check_message_valid(msg)
        cmd = msg[2:4]
        decoder = getattr(self, '_{}_decode'.format(cmd.lower()), None)
        if not decoder:
            cmd = 'unknown'
            decoder = self._unknown_decode
        decoded_msg = decoder(msg)
        for handler in self._handlers.get(cmd, []):
            handler(**decoded_msg)

    def _am_decode(self, msg):
        """AM: Alarm memory by area report."""
        return {'alarm_memory': [x for x in msg[4:4+Max.AREAS.value]]}

    def _as_decode(self, msg):
        """AS: Arming status report."""
        return {'armed_statuses': [x for x in msg[4:12]],
                'arm_up_states': [x for x in msg[12:20]],
                'alarm_states': [x for x in msg[20:28]]}

    def _az_decode(self, msg):
        """AZ: Alarm by zone report."""
        return {'alarm_status': [x for x in msg[4:4+Max.ZONES.value]]}

    def _cr_one_custom_value_decode(self, index, part):
        value = int(part[0:5])
        value_format = int(part[5])
        if value_format == 2:
            value = ((value >> 8) & 0xff, value & 0xff)
        return {'index': index, 'value': value, 'value_format': value_format}

    def _cr_decode(self, msg):
        """CR: Custom values"""
        if int(msg[4:6]) > 0:
            index = int(msg[4:6])-1
            return {'values': [self._cr_one_custom_value_decode(index, msg[6:12])]}
        else:
            part = 6
            ret = []
            for i in range(Max.SETTINGS.value):
                ret.append(self._cr_one_custom_value_decode(i, msg[part:part+6]))
                part += 6
            return {'values': ret}

    def _cc_decode(self, msg):
        """CC: Output status for single output."""
        return {'output': int(msg[4:7])-1, 'output_status': msg[7] == '1'}

    def _cs_decode(self, msg):
        """CS: Output status for all outputs."""
        output_status = [x == '1' for x in msg[4:4+Max.OUTPUTS.value]]
        return {'output_status': output_status}

    def _cv_decode(self, msg):
        """CV: Counter value."""
        return {'counter': int(msg[4:6])-1, 'value': int(msg[6:11])}

    def _ee_decode(self, msg):
        """EE: Entry/exit timer report."""
        return {'area': int(msg[4:5])-1, 'is_exit': msg[5:6] == '0',
                'timer1': int(msg[6:9]), 'timer2': int(msg[9:12]),
                'armed_status': msg[12:13]}

    def _ic_decode(self, msg):
        """IC: Send Valid Or Invalid User Code Format."""
        code = msg[4:16]
        if re.match(r'(0\d){6}', code):
            code = re.sub(r'0(\d)', r'\1', code)
        return {'code': code, 'user': int(msg[16:19])-1,
                'keypad': int(msg[19:21])-1}

    def _ie_decode(self, _msg):
        """IE: Installer mode exited."""
        return {}

    def _ka_decode(self, msg):
        """KA: Keypad areas for all keypads."""
        return {'keypad_areas': [ord(x)-0x31 for x in msg[4:4+Max.KEYPADS.value]]}

    def _kc_decode(self, msg):
        """KC: Keypad key change."""
        return {'keypad': int(msg[4:6])-1, 'key': int(msg[6:8])}

    def _lw_decode(self, msg):
        """LW: temperatures from all keypads and zones 1-16."""
        keypad_temps = []
        zone_temps = []
        for i in range(16):
            keypad_temps.append(int(msg[4+3*i:7+3*i]) - 40)
            zone_temps.append(int(msg[52+3*i:55+3*i]) - 60)
        return {'keypad_temps': keypad_temps, 'zone_temps': zone_temps}

    def _pc_decode(self, msg):
        """PC: PLC (lighting) change."""
        housecode = msg[4:7]
        return {'housecode': housecode, 'index': housecode_to_index(housecode),
                'light_level': int(msg[7:9])}

    def _ps_decode(self, msg):
        """PS: PLC (lighting) status."""
        return {'bank': ord(msg[4]) - 0x30,
                'statuses': [ord(x)-0x30 for x in msg[5:69]]}

    def _rp_decode(self, msg):
        """RP: Remote programming status."""
        return {'remote_programming_status': int(msg[4:6])}

    def _sd_decode(self, msg):
        """SD: Description text."""
        desc_ch1 = msg[9]
        show_on_keypad = ord(desc_ch1) >= 0x80
        if show_on_keypad:
            desc_ch1 = chr(ord(desc_ch1) & 0x7f)
        return {'desc_type': int(msg[4:6]), 'unit': int(msg[6:9])-1,
                'desc': (desc_ch1+msg[10:25]).rstrip(),
                'show_on_keypad': show_on_keypad}

    def _ss_decode(self, msg):
        """SS: System status."""
        return {'system_trouble_status': msg[4:-2]}

    def _st_decode(self, msg):
        """ST: Temperature update."""
        group = int(msg[4:5])
        temperature = int(msg[7:10])
        if group == 0:
            temperature -= 60
        elif group == 1:
            temperature -= 40
        return {'group': group, 'device': int(msg[5:7])-1,
                'temperature': temperature}

    def _tc_decode(self, msg):
        """TC: Task change."""
        return {'task': int(msg[4:7])-1}

    def _tr_decode(self, msg):
        """TR: Thermostat data response."""
        return {'thermostat_index': int(msg[4:6])-1, 'mode': int(msg[6]),
                'hold': msg[7] == '1', 'fan': int(msg[8]),
                'current_temp': int(msg[9:11]), 'heat_setpoint': int(msg[11:13]),
                'cool_setpoint': int(msg[13:15]), 'humidity': int(msg[15:17])}

    def _vn_decode(self, msg):
        """VN: Version information."""
        elkm1_version = "{}.{}.{}".format(int(msg[4:6], 16), int(msg[6:8], 16),
                                          int(msg[8:10], 16))
        xep_version = "{}.{}.{}".format(int(msg[10:12], 16), int(msg[12:14], 16),
                                        int(msg[14:16], 16))
        return {'elkm1_version': elkm1_version, 'xep_version': xep_version}

    def _xk_decode(self, msg):
        """XK: Ethernet Test."""
        return {'real_time_clock': msg[4:20]}

    def _zb_decode(self, msg):
        """ZB: Zone bypass report."""
        return {'zone_number': int(msg[4:7])-1, 'zone_bypassed': msg[7] == '1'}

    def _zc_decode(self, msg):
        """ZC: Zone Change."""
        status = _status_decode(int(msg[7:8], 16))
        return {'zone_number': int(msg[4:7])-1, 'zone_status': status}

    def _zd_decode(self, msg):
        """ZD: Zone definitions."""
        zone_definitions = [ord(x)-0x30 for x in msg[4:4+Max.ZONES.value]]
        return {'zone_definitions': zone_definitions}

    def _zp_decode(self, msg):
        """ZP: Zone partitions."""
        zone_partitions = [ord(x)-0x31 for x in msg[4:4+Max.ZONES.value]]
        return {'zone_partitions': zone_partitions}

    def _zs_decode(self, msg):
        """ZS: Zone statuses."""
        status = [_status_decode(int(x, 16)) for x in msg[4:4+Max.ZONES.value]]
        return {'zone_statuses': status}

    def _zv_decode(self, msg):
        """ZV: Zone voltage."""
        return {'zone_number': int(msg[4:7])-1, 'zone_voltage': int(msg[7:10])/10}

    def _unknown_decode(self, msg):
        """Generic handler called when no specific handler exists"""
        return {'msg_code': msg[2:4], 'data': msg[4:-2]}

    # def timeout_decode(self, msg_code):
    #     """Called directly when a timeout happens when response not received"""
    #     return {'msg_code': msg_code}


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
