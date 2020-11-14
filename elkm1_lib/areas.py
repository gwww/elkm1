"""Definition of an ElkM1 Area"""

from .const import ArmedStatus, Max, TextDescriptions
from .elements import Element, Elements
from .message import al_encode, as_encode, az_encode, dm_encode, zb_encode


class Area(Element):  # pylint: disable=too-many-instance-attributes
    """Class representing an Area"""

    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.armed_status = None
        self.arm_up_state = None
        self.alarm_state = None
        self.alarm_memory = None
        self.is_exit = False
        self.timer1 = 0
        self.timer2 = 0
        self.last_log = None

    def is_armed(self):
        """Return if the area is armed."""
        return self.armed_status != ArmedStatus.DISARMED.value

    def arm(self, level, code):
        """(Helper) Arm system at specified level (away, vacation, etc)"""
        if self.is_armed() and level > "0":
            return
        self._elk.send(al_encode(level, self._index, code))

    def disarm(self, code):
        """(Helper) Disarm system."""
        self.arm("0", code)

    def display_message(
        self, clear, beep, timeout, line1, line2
    ):  # pylint: disable=too-many-arguments
        """(Helper) Display a message on all of the keypads in this area."""
        self._elk.send(dm_encode(self._index, clear, beep, timeout, line1, line2))

    def bypass(self, code):
        """(Helper) Bypass area."""
        self._elk.send(zb_encode(999, self._index, code))

    def clear_bypass(self, code):
        """(Helper) Clear bypass area."""
        self._elk.send(zb_encode(-1, self._index, code))


class Areas(Elements):
    """Handling for multiple areas"""

    def __init__(self, elk):
        super().__init__(elk, Area, Max.AREAS.value)
        elk.add_handler("AM", self._am_handler)
        elk.add_handler("AS", self._as_handler)
        elk.add_handler("EE", self._ee_handler)
        elk.add_handler("LD", self._ld_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.elk.send(as_encode())
        self.get_descriptions(TextDescriptions.AREA.value)

    def _am_handler(self, alarm_memory):
        for area in self.elements:
            area.setattr("alarm_memory", alarm_memory[area.index], True)

    def _as_handler(self, armed_statuses, arm_up_states, alarm_states):
        update_alarm_triggers = False
        for area in self.elements:
            area.setattr("armed_status", armed_statuses[area.index], False)
            area.setattr("arm_up_state", arm_up_states[area.index], False)
            if (
                area.alarm_state != alarm_states[area.index]
                or alarm_states[area.index] != "0"
            ):
                update_alarm_triggers = True
            area.setattr("alarm_state", alarm_states[area.index], True)

        if update_alarm_triggers:
            self.elk.send(az_encode())

    def _ee_handler(
        self, area, is_exit, timer1, timer2, armed_status
    ):  # pylint: disable=too-many-arguments
        area = self.elements[area]
        area.setattr("armed_status", armed_status, False)
        area.setattr("timer1", timer1, False)
        area.setattr("timer2", timer2, False)
        area.setattr("is_exit", is_exit, True)

    # ElkM1 global setting G35 must be set for LD messages to be sent
    def _ld_handler(self, area, log):
        if log["event"] in [1173, 1174]:
            # arm/disarm log (YAGNI - decode number for more log types when needed)
            log["user_number"] = log["number"]
        self.elements[area].setattr("last_log", log, True)
