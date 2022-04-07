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

from __future__ import annotations

import datetime as dt
import re
import time
from collections import namedtuple
from collections.abc import Callable
from typing import Any, cast

from .const import Max

MessageEncode = namedtuple("MessageEncode", ["message", "response_command"])
# MsgHandler = Callable[[dict[str, Any]], None] # Gives type error
MsgHandler = Callable[..., None]

# pylint: disable=no-self-use
class MessageDecode:
    """Message decode and dispatcher."""

    def __init__(self) -> None:
        """Initialize a new Message instance."""
        self._handlers: dict[str, list[MsgHandler]] = {}

    def add_handler(self, message_type: str, handler: MsgHandler) -> None:
        """Add callback for handlers."""
        if message_type not in self._handlers:
            self._handlers[message_type] = []

        if handler not in self._handlers[message_type]:
            self._handlers[message_type].append(handler)

    def remove_handler(self, message_type: str, handler: MsgHandler) -> None:
        """Remove callback for handlers."""
        if message_type not in self._handlers:
            return
        if handler in self._handlers[message_type]:
            self._handlers[message_type].remove(handler)

    def call_handlers(self, cmd: str, decoded_msg: dict[str, Any]) -> None:
        """Call the message handlers."""
        # Copy the handlers list as add/remove could be
        # called when invoking the handlers
        handlers = list(self._handlers.get(cmd, []))

        for handler in handlers:
            handler(**decoded_msg)

    def decode(self, msg: str) -> None:
        """Decode an Elk message by passing to appropriate decoder"""
        valid, error_msg = _is_valid_length_and_checksum(msg)
        if valid:
            cmd = msg[2:4]
            decoder = getattr(self, f"_{cmd.lower()}_decode", None)
            if not decoder:
                cmd = "unknown"
                decoder = self._unknown_decode
            try:
                self.call_handlers(cmd, decoder(msg))
            except (IndexError, ValueError) as exc:
                raise ValueError("Cannot decode message") from exc
            return

        if not msg or msg.startswith("Username: ") or msg.startswith("Password: "):
            return
        if "Login successful" in msg:
            self.call_handlers("login", {"succeeded": True})
        elif msg.startswith("Username/Password not found") or msg == "Disabled":
            self.call_handlers("login", {"succeeded": False})
        else:
            raise ValueError(error_msg)

    def _am_decode(self, msg: str) -> dict[str, str]:
        """AM: Alarm memory by area report."""
        return {"alarm_memory": msg[4 : 4 + Max.AREAS.value]}

    def _as_decode(self, msg: str) -> dict[str, str]:
        """AS: Arming status report."""
        return {
            "armed_statuses": msg[4:12],
            "arm_up_states": msg[12:20],
            "alarm_states": msg[20:28],
        }

    def _az_decode(self, msg: str) -> dict[str, str]:
        """AZ: Alarm by zone report."""
        return {"alarm_status": msg[4 : 4 + Max.ZONES.value]}

    def _cr_one_custom_value_decode(self, index: int, part: str) -> dict[str, Any]:
        value = int(part[0:5])
        value_format = int(part[5])
        if value_format == 2:
            ret: int | tuple[int, int] = ((value >> 8) & 0xFF, value & 0xFF)
        else:
            ret = value
        return {"index": index, "value": ret, "value_format": value_format}

    def _cr_decode(self, msg: str) -> dict[str, Any]:
        """CR: Custom values"""
        if int(msg[4:6]) > 0:
            index = int(msg[4:6]) - 1
            return {"values": [self._cr_one_custom_value_decode(index, msg[6:12])]}

        part = 6
        ret = []
        for i in range(Max.SETTINGS.value):
            ret.append(self._cr_one_custom_value_decode(i, msg[part : part + 6]))
            part += 6
        return {"values": ret}

    def _cc_decode(self, msg: str) -> dict[str, Any]:
        """CC: Output status for single output."""
        return {"output": int(msg[4:7]) - 1, "output_status": msg[7] == "1"}

    def _cs_decode(self, msg: str) -> dict[str, Any]:
        """CS: Output status for all outputs."""
        output_status = [x == "1" for x in msg[4 : 4 + Max.OUTPUTS.value]]
        return {"output_status": output_status}

    def _cv_decode(self, msg: str) -> dict[str, Any]:
        """CV: Counter value."""
        return {"counter": int(msg[4:6]) - 1, "value": int(msg[6:11])}

    def _ee_decode(self, msg: str) -> dict[str, Any]:
        """EE: Entry/exit timer report."""
        return {
            "area": int(msg[4:5]) - 1,
            "is_exit": msg[5:6] == "0",
            "timer1": int(msg[6:9]),
            "timer2": int(msg[9:12]),
            "armed_status": msg[12:13],
        }

    def _ic_decode(self, msg: str) -> dict[str, Any]:
        """IC: Send Valid Or Invalid User Code Format."""
        code = msg[4:16]
        if re.match(r"(0\d){6}", code):
            code = re.sub(r"0(\d)", r"\1", code)
        return {
            "code": code,
            "user": int(msg[16:19]) - 1,
            "keypad": int(msg[19:21]) - 1,
        }

    def _ie_decode(self, _msg: str) -> dict[str, str]:
        """IE: Installer mode exited."""
        return {}

    def _ka_decode(self, msg: str) -> dict[str, Any]:
        """KA: Keypad areas for all keypads."""
        return {"keypad_areas": [ord(x) - 0x31 for x in msg[4 : 4 + Max.KEYPADS.value]]}

    def _kc_decode(self, msg: str) -> dict[str, Any]:
        """KC: Keypad key change."""
        return {"keypad": int(msg[4:6]) - 1, "key": int(msg[6:8])}

    def _ld_decode(self, msg: str) -> dict[str, Any]:
        """LD: System Log Data Update."""
        area = int(msg[11]) - 1
        hour = int(msg[12:14])
        minute = int(msg[14:16])
        month = int(msg[16:18])
        day = int(msg[18:20])
        year = int(msg[24:26]) + 2000
        log_local_datetime = dt.datetime(year, month, day, hour, minute)
        log_local_time = time.mktime(log_local_datetime.timetuple())
        log_gm_timestruct = time.gmtime(log_local_time)

        log: dict[str, Any] = {}
        log["event"] = int(msg[4:8])
        log["number"] = int(msg[8:11])
        log["index"] = int(msg[20:23])
        log["timestamp"] = dt.datetime(
            *log_gm_timestruct[:6], tzinfo=dt.timezone.utc
        ).isoformat()

        return {"area": area, "log": log}

    def _lw_decode(self, msg: str) -> dict[str, Any]:
        """LW: temperatures from all keypads and zones 1-16."""
        keypad_temps = []
        zone_temps = []
        for i in range(16):
            keypad_temps.append(int(msg[4 + 3 * i : 7 + 3 * i]) - 40)
            zone_temps.append(int(msg[52 + 3 * i : 55 + 3 * i]) - 60)
        return {"keypad_temps": keypad_temps, "zone_temps": zone_temps}

    def _pc_decode(self, msg: str) -> dict[str, Any]:
        """PC: PLC (lighting) change."""
        housecode = msg[4:7]
        return {
            "housecode": housecode,
            "index": housecode_to_index(housecode),
            "light_level": int(msg[7:9]),
        }

    def _ps_decode(self, msg: str) -> dict[str, Any]:
        """PS: PLC (lighting) status."""
        return {
            "bank": ord(msg[4]) - 0x30,
            "statuses": [ord(x) - 0x30 for x in msg[5:69]],
        }

    def _rp_decode(self, msg: str) -> dict[str, int]:
        """RP: Remote programming status."""
        return {"remote_programming_status": int(msg[4:6])}

    def _rr_decode(self, msg: str) -> dict[str, str]:
        """RR: Realtime clock."""
        return {"real_time_clock": msg[4:20]}

    def _sd_decode(self, msg: str) -> dict[str, Any]:
        """SD: Description text."""
        desc_ch1 = msg[9]
        show_on_keypad = ord(desc_ch1) >= 0x80
        if show_on_keypad:
            desc_ch1 = chr(ord(desc_ch1) & 0x7F)
        return {
            "desc_type": int(msg[4:6]),
            "unit": int(msg[6:9]) - 1,
            "desc": (desc_ch1 + msg[10:25]).rstrip(),
            "show_on_keypad": show_on_keypad,
        }

    def _ss_decode(self, msg: str) -> dict[str, str]:
        """SS: System status."""
        return {"system_trouble_status": msg[4:-2]}

    def _st_decode(self, msg: str) -> dict[str, Any]:
        """ST: Temperature update."""
        group = int(msg[4:5])
        temperature = int(msg[7:10])
        if group == 0:
            temperature -= 60
        elif group == 1:
            temperature -= 40
        return {"group": group, "device": int(msg[5:7]) - 1, "temperature": temperature}

    def _tc_decode(self, msg: str) -> dict[str, int]:
        """TC: Task change."""
        return {"task": int(msg[4:7]) - 1}

    def _tr_decode(self, msg: str) -> dict[str, Any]:
        """TR: Thermostat data response."""
        return {
            "thermostat_index": int(msg[4:6]) - 1,
            "mode": int(msg[6]),
            "hold": msg[7] == "1",
            "fan": int(msg[8]),
            "current_temp": int(msg[9:11]),
            "heat_setpoint": int(msg[11:13]),
            "cool_setpoint": int(msg[13:15]),
            "humidity": int(msg[15:17]),
        }

    def _ua_decode(self, msg: str) -> dict[str, Any]:
        """UA: Valid User Code Areas."""
        return {
            "user_code": int(msg[4:10]),
            "valid_areas": int(msg[10:12], 16),
            "diagnostic": msg[12:20],
            "user_code_length": int(msg[20]),
            "user_code_type": int(msg[21]),
            "temperature_units": msg[22],
        }

    def _vn_decode(self, msg: str) -> dict[str, str]:
        """VN: Version information."""
        elkm1_version = f"{int(msg[4:6], 16)}.{int(msg[6:8], 16)}.{int(msg[8:10], 16)}"
        xep_version = (
            f"{int(msg[10:12], 16)}.{int(msg[12:14], 16)}.{int(msg[14:16], 16)}"
        )
        return {"elkm1_version": elkm1_version, "xep_version": xep_version}

    def _xk_decode(self, msg: str) -> dict[str, str]:
        """XK: Ethernet Test."""
        return {"real_time_clock": msg[4:20]}

    def _zb_decode(self, msg: str) -> dict[str, Any]:
        """ZB: Zone bypass report."""
        return {"zone_number": int(msg[4:7]) - 1, "zone_bypassed": msg[7] == "1"}

    def _zc_decode(self, msg: str) -> dict[str, Any]:
        """ZC: Zone Change."""
        status = _status_decode(int(msg[7:8], 16))
        return {"zone_number": int(msg[4:7]) - 1, "zone_status": status}

    def _zd_decode(self, msg: str) -> dict[str, list[int]]:
        """ZD: Zone definitions."""
        zone_definitions = [ord(x) - 0x30 for x in msg[4 : 4 + Max.ZONES.value]]
        return {"zone_definitions": zone_definitions}

    def _zp_decode(self, msg: str) -> dict[str, list[int]]:
        """ZP: Zone partitions."""
        zone_partitions = [ord(x) - 0x31 for x in msg[4 : 4 + Max.ZONES.value]]
        return {"zone_partitions": zone_partitions}

    def _zs_decode(self, msg: str) -> dict[str, list[tuple[int, int]]]:
        """ZS: Zone statuses."""
        status = [_status_decode(int(x, 16)) for x in msg[4 : 4 + Max.ZONES.value]]
        return {"zone_statuses": status}

    def _zv_decode(self, msg: str) -> dict[str, Any]:
        """ZV: Zone voltage."""
        return {"zone_number": int(msg[4:7]) - 1, "zone_voltage": int(msg[7:10]) / 10}

    def _unknown_decode(self, msg: str) -> dict[str, str]:
        """Generic handler called when no specific handler exists"""
        return {"msg_code": msg[2:4], "data": msg[4:-2]}


# pylint: enable=no-self-use


def housecode_to_index(housecode: str) -> int:
    """Convert a X10 housecode to a zero-based index"""
    match = re.search(r"^([A-P])(\d{1,2})$", housecode.upper())
    if match:
        house_index = int(match.group(2))
        if 1 <= house_index <= 16:
            return (ord(match.group(1)) - ord("A")) * 16 + house_index - 1
    raise ValueError("Invalid X10 housecode: %s" % housecode)


def index_to_housecode(index: int) -> str:
    """Convert a zero-based index to a X10 housecode."""
    if index < 0 or index > 255:
        raise ValueError
    quotient, remainder = divmod(index, 16)
    return f"{chr(ord('A') + quotient)}{remainder + 1:02}"


def get_elk_command(line: str) -> str:
    """Return the 2 character command in the message."""
    if len(line) < 4:
        return ""
    return line[2:4]


def _status_decode(status: int) -> tuple[int, int]:
    """Decode a 1 byte status into logical and physical statuses."""
    logical_status = (status & 0b00001100) >> 2
    physical_status = status & 0b00000011
    return (logical_status, physical_status)


def _is_valid_length_and_checksum(msg: str) -> tuple[bool, str]:
    """Check packet length valid and that checksum is good."""
    try:
        if int(msg[:2], 16) != (len(msg) - 2):
            return False, "Incorrect message length"

        checksum = int(msg[-2:], 16)
        for char in msg[:-2]:
            checksum += ord(char)
        if (checksum % 256) != 0:
            return False, "Bad checksum"
    except ValueError:
        return False, "Message invalid"

    return True, ""


def al_encode(arm_mode: str, area: int, user_code: int) -> MessageEncode:
    """al: Arm system. Note in 'al' the 'l' can vary"""
    return MessageEncode(f"0Da{arm_mode}{area + 1:1}{user_code:06}00", "AS")


def as_encode() -> MessageEncode:
    """as: Get area status."""
    return MessageEncode("06as00", "AS")


def az_encode() -> MessageEncode:
    """az: Get alarm by zone."""
    return MessageEncode("06az00", "AZ")


def cf_encode(output: int) -> MessageEncode:
    """cf: Turn off output."""
    return MessageEncode(f"09cf{output + 1:03}00", None)


def ct_encode(output: int) -> MessageEncode:
    """ct: Toggle output."""
    return MessageEncode(f"09ct{output + 1:03}00", None)


def cn_encode(output: int, seconds: int) -> MessageEncode:
    """cn: Turn on output."""
    return MessageEncode(f"0Ecn{output + 1:03}{seconds:05}00", None)


def cs_encode() -> MessageEncode:
    """cs: Get all output status."""
    return MessageEncode("06cs00", "CS")


def cp_encode() -> MessageEncode:
    """cp: Get ALL custom values."""
    return MessageEncode("06cp00", "CR")


def cr_encode(index: int) -> MessageEncode:
    """cr: Get a custom value."""
    return MessageEncode(f"08cr{index + 1:02}00", "CR")


def cw_encode(
    index: int, value: int | tuple[int, int], value_format: int
) -> MessageEncode:
    """cw: Write a custom value."""
    if value_format == 2:
        x = cast(tuple[int, int], value)
        enc = x[0] * 256 + x[1]
    else:
        enc = cast(int, value)
    return MessageEncode(f"0Dcw{index + 1:02}{enc:05}00", None)


def cv_encode(counter: int) -> MessageEncode:
    """cv: Get counter."""
    return MessageEncode(f"08cv{counter + 1:02}00", "CV")


def cx_encode(counter: int, value: int) -> MessageEncode:
    """cx: Change counter value."""
    return MessageEncode(f"0Dcx{counter + 1:02}{value:05}00", "CV")


def dm_encode(
    keypad_area: int, clear: int, beep: bool, timeout: int, line1: str, line2: str
) -> MessageEncode:  # pylint: disable=too-many-arguments
    """dm: Display message on keypad."""
    return MessageEncode(
        f"2Edm{keypad_area + 1:1}{clear:1}{beep:1}{timeout:05}{line1:^<16.16}{line2:^<16.16}00",
        None,
    )


def ka_encode() -> MessageEncode:
    """ka: Get keypad areas."""
    return MessageEncode("06ka00", "KA")


def lw_encode() -> MessageEncode:
    """lw: Get temperature data."""
    return MessageEncode("06lw00", "LW")


def pc_encode(
    index: int, function_code: int, extended_code: int, seconds: int
) -> MessageEncode:
    """pc: Control any PLC device."""
    return MessageEncode(
        f"11pc{index_to_housecode(index)}{function_code:02}{extended_code:02}{seconds:04}00",
        None,
    )


def pf_encode(index: int) -> MessageEncode:
    """pf: Turn off light."""
    return MessageEncode(f"09pf{index_to_housecode(index)}00", None)


def pn_encode(index: int) -> MessageEncode:
    """pn: Turn on light."""
    return MessageEncode(f"09pn{index_to_housecode(index)}00", None)


def ps_encode(bank: int) -> MessageEncode:
    """ps: Get lighting status."""
    return MessageEncode(f"07ps{bank:1}00", "PS")


def pt_encode(index: int) -> MessageEncode:
    """pt: Toggle light."""
    return MessageEncode(f"09pt{index_to_housecode(index)}00", None)


def sd_encode(desc_type: int, unit: int) -> MessageEncode:
    """sd: Get description."""
    return MessageEncode(f"0Bsd{desc_type:02}{unit + 1:03}00", "SD")


def sp_encode(phrase: int) -> MessageEncode:
    """sp: Speak phrase."""
    return MessageEncode(f"09sp{phrase:03}00", None)


def ss_encode() -> MessageEncode:
    """ss: Get system trouble status."""
    return MessageEncode("06ss00", "SS")


def sw_encode(word: int) -> MessageEncode:
    """sw: Speak word."""
    return MessageEncode(f"09sw{word:03}00", None)


def rw_encode(date_time: dt.datetime) -> MessageEncode:
    """rw: Write time given a datetime."""
    elk_weekday = (date_time.weekday() + 1) % 7 + 1
    time_str = date_time.strftime("%S%M%H.%d%m%y").replace(".", str(elk_weekday))
    return MessageEncode(f"13rw{time_str}00", None)


def tn_encode(task: int) -> MessageEncode:
    """tn: Activate task."""
    return MessageEncode(f"09tn{task + 1:03}00", None)


def tr_encode(thermostat: int) -> MessageEncode:
    """tr: Request thermostat data."""
    return MessageEncode(f"08tr{thermostat + 1:02}00", None)


def ts_encode(thermostat: int, value: int, element: int) -> MessageEncode:
    """ts: Set thermostat data."""
    return MessageEncode(f"0Bts{thermostat + 1:02}{value:02}{element:1}00", None)


def ua_encode(user_code: int) -> MessageEncode:
    """ua: Requst valid user code areas"""
    return MessageEncode(f"0Cua{user_code:06}00", "UA")


def vn_encode() -> MessageEncode:
    """zd: Get panel software version information."""
    return MessageEncode("06vn00", "VN")


def zb_encode(zone: int, area: int, user_code: int) -> MessageEncode:
    """zb: Zone bypass. Zone < 0 unbypass all; Zone > Max bypass all."""
    if zone < 0:
        zone = 0
    elif zone > Max.ZONES.value:
        zone = 999
    else:
        zone += 1
    return MessageEncode(
        f"10zb{zone:03}{area + 1:1}{user_code:06}00",
        "ZB",
    )


def zd_encode() -> MessageEncode:
    """zd: Get zone definitions"""
    return MessageEncode("06zd00", "ZD")


def zp_encode() -> MessageEncode:
    """zp: Get zone partitions"""
    return MessageEncode("06zp00", "ZP")


def zs_encode() -> MessageEncode:
    """zs: Get zone statuses"""
    return MessageEncode("06zs00", "ZS")


def zt_encode(zone: int) -> MessageEncode:
    """zt: Trigger zone."""
    return MessageEncode(f"09zt{zone + 1:03}00", None)


def zv_encode(zone: int) -> MessageEncode:
    """zv: Get zone voltage"""
    return MessageEncode(f"09zv{zone + 1:03}00", "ZV")
