"""Definition of an ElkM1 Area"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, as_encode, al_encode


class Area(Element):
    """Class representing an Area"""
    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.armed_status = None
        self.arm_up_state = None
        self.alarm_state = None

    def arm(self, level, code):
        """(Helper) Arm system at specified level (away, vacation, etc)"""
        self.elk.send(al_encode(level, self._index, code))

    def disarm(self, code):
        """(Helper) Disarm system."""
        self.arm(0, code)

class Areas(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, Area, Max.AREAS.value)
        add_message_handler('AS', self._as_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.elk.send(as_encode())
        self.get_descriptions(TextDescriptions.AREA.value)

    def _as_handler(self, armed_statuses, arm_up_states, alarm_states):
        for area in self.elements:
            area.setattr('armed_status', armed_statuses[area.index])
            area.setattr('arm_up_state', arm_up_states[area.index])
            area.setattr('alarm_state', alarm_states[area.index])
