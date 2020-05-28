"""Definition of an ElkM1 Area"""

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import as_encode, az_encode, al_encode, dm_encode


class Area(Element):
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
        # these correspond to the most recent LD log data event
        self.log_event = None
        self.log_number = None
        self.log_area = None
        self.log_hour = None
        self.log_minute = None
        self.log_month = None
        self.log_day = None
        self.log_index = None
        self.log_day_of_week = None
        self.log_year = None

    def arm(self, level, code):
        """(Helper) Arm system at specified level (away, vacation, etc)"""
        self._elk.send(al_encode(level, self._index, code))

    def disarm(self, code):
        """(Helper) Disarm system."""
        self.arm(0, code)

    def display_message(self, clear, beep, timeout, line1, line2):
        """Display a message on all of the keypads in this area."""
        self._elk.send(dm_encode(self._index, clear, beep, timeout, line1, line2))


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

    # pylint: disable=too-many-arguments
    def _ee_handler(self, area, is_exit, timer1, timer2, armed_status):
        area = self.elements[area]
        area.setattr("armed_status", armed_status, False)
        area.setattr("timer1", timer1, False)
        area.setattr("timer2", timer2, False)
        area.setattr("is_exit", is_exit, True)

    # note the LD message are only output by the system when
    # the G29 "Special" global setting "Event log" checkbox is set
    def _ld_handler(self, event, number, area,
                    hour, minute,
                    month, day, index,
                    day_of_week, year):
        a = self.elements[area]
        a.setattr("log_event", event, False)
        a.setattr("log_number", number, False)
        a.setattr("log_area", area, False)
        a.setattr("log_hour", hour, False)
        a.setattr("log_minute", minute, False)
        a.setattr("log_month", month, False)
        a.setattr("log_day", day, False)
        a.setattr("log_index", index, False)
        a.setattr("log_day_of_week", day_of_week, False)
        a.setattr("log_year", year, True)
