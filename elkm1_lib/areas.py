"""Definition of an ElkM1 Area"""

from __future__ import annotations

from typing import Any, cast

from .connection import Connection
from .const import ArmedStatus, Max, TextDescriptions
from .elements import Element, Elements
from .message import al_encode, as_encode, az_encode, dm_encode, zb_encode


class Area(Element):
    """Class representing an Area"""

    def __init__(self, index: int, connection: Connection) -> None:
        super().__init__(index, connection)
        self.armed_status: str | None = None
        self.arm_up_state: str | None = None
        self.alarm_state: str | None = None
        self.alarm_memory: str | None = None
        self.is_exit = False
        self.timer1 = 0
        self.timer2 = 0
        self.last_log: str | None = None

    def is_armed(self) -> bool:
        """Return if the area is armed."""
        return self.armed_status != ArmedStatus.DISARMED.value

    def arm(self, level: str, code: int) -> None:
        """(Helper) Arm system at specified level (away, vacation, etc)"""
        if self.is_armed() and level > "0":
            return
        self._connection.send(al_encode(level, self._index, code))

    def disarm(self, code: int) -> None:
        """(Helper) Disarm system."""
        self.arm("0", code)

    def display_message(
        self, clear: int, beep: bool, timeout: int, line1: str, line2: str
    ) -> None:
        """(Helper) Display a message on all of the keypads in this area."""
        self._connection.send(
            dm_encode(self._index, clear, beep, timeout, line1, line2)
        )

    def bypass(self, code: int) -> None:
        """(Helper) Bypass area."""
        self._connection.send(zb_encode(999, self._index, code))

    def clear_bypass(self, code: int) -> None:
        """(Helper) Clear bypass area."""
        self._connection.send(zb_encode(-1, self._index, code))


class Areas(Elements):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection) -> None:
        super().__init__(connection, Area, Max.AREAS.value)
        connection.msg_decode.add_handler("AM", self._am_handler)
        connection.msg_decode.add_handler("AS", self._as_handler)
        connection.msg_decode.add_handler("EE", self._ee_handler)
        connection.msg_decode.add_handler("LD", self._ld_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self._connection.send(as_encode())
        self.get_descriptions(TextDescriptions.AREA.value)

    def _am_handler(self, alarm_memory: str) -> None:
        for area in self.elements:
            area.setattr("alarm_memory", alarm_memory[area.index], True)

    def _as_handler(
        self, armed_statuses: str, arm_up_states: str, alarm_states: str
    ) -> None:
        update_alarm_triggers = False
        for area in self.elements:
            area = cast(Area, area)
            area.setattr("armed_status", armed_statuses[area.index], False)
            area.setattr("arm_up_state", arm_up_states[area.index], False)
            if (
                area.alarm_state != alarm_states[area.index]
                or alarm_states[area.index] != "0"
            ):
                update_alarm_triggers = True
            area.setattr("alarm_state", alarm_states[area.index], True)

        if update_alarm_triggers:
            self._connection.send(az_encode())

    def _ee_handler(
        self, area: int, is_exit: bool, timer1: int, timer2: int, armed_status: str
    ) -> None:
        area_element = cast(Area, self.elements[area])
        area_element.setattr("armed_status", armed_status, False)
        area_element.setattr("timer1", timer1, False)
        area_element.setattr("timer2", timer2, False)
        area_element.setattr("is_exit", is_exit, True)

    # ElkM1 global setting G35 must be set for LD messages to be sent
    def _ld_handler(self, area: int, log: dict[str, Any]) -> None:
        if log["event"] in [1173, 1174]:
            # arm/disarm log (YAGNI - decode number for more log types when needed)
            log["user_number"] = log["number"]
        self.elements[area].setattr("last_log", log, True)
