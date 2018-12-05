"""Definition of an ElkM1 Area"""

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, as_encode, al_encode, dm_encode


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

    def arm(self, level, code):
        """(Helper) Arm system at specified level (away, vacation, etc)"""
        self._elk.send(al_encode(level, self._index, code))

    def disarm(self, code):
        """(Helper) Disarm system."""
        self.arm(0, code)

    def display_message(self, clear, beep, timeout, line1, line2):
        """Display a message on all of the keypads in this area."""
        self._elk.send(
            dm_encode(self._index, clear, beep, timeout, line1, line2)
        )


class Areas(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, Area, Max.AREAS.value)
        add_message_handler('AM', self._am_handler)
        add_message_handler('AS', self._as_handler)
        add_message_handler('EE', self._ee_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.elk.send(as_encode())
        self.get_descriptions(TextDescriptions.AREA.value)

    def _am_handler(self, alarm_memory):
        for area in self.elements:
            area.setattr('alarm_memory', alarm_memory[area.index], True)

    def _as_handler(self, armed_statuses, arm_up_states, alarm_states):
        for area in self.elements:
            area.setattr('armed_status', armed_statuses[area.index], False)
            area.setattr('arm_up_state', arm_up_states[area.index], False)
            area.setattr('alarm_state', alarm_states[area.index], True)

    # pylint: disable=too-many-arguments
    def _ee_handler(self, area, is_exit, timer1, timer2, armed_status):
        area = self.elements[area]
        area.setattr('armed_status', armed_status, False)
        area.setattr('timer1', timer1, False)
        area.setattr('timer2', timer2, False)
        area.setattr('is_exit', is_exit, True)
