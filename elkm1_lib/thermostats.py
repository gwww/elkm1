"""Definition of an ElkM1 Thermostat"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, tr_encode, ts_encode


class Thermostat(Element):
    """Class representing an Thermostat"""
    def __init__(self, index, elk):  # pylint: disable=useless-super-delegation
        super().__init__(index, elk)
        self.mode = 0
        self.hold = False
        self.fan = 0
        self.current_temp = 0
        self.heat_setpoint = 0
        self.cool_setpoint = 0
        self.humidity = 0

    def set(self, element_to_set, value):
        """(Helper) Set thermostat"""
        self._elk.send(ts_encode(self.index, value, element_to_set))


class Thermostats(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, Thermostat, Max.THERMOSTATS.value)
        add_message_handler('ST', self._st_handler)
        add_message_handler('TR', self._tr_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.THERMOSTAT.value)

    def _got_desc(self, descriptions):
        super()._got_desc(descriptions)
        # Only poll thermostats that have a name defined
        for thermostat in self.elements:
            if not thermostat.is_default_name():
                self.elk.send(tr_encode(thermostat.index))

    def _st_handler(self, group, device, temperature):
        if group == 2:
            self.elements[device].setattr('current_temp', temperature, True)

    # pylint: disable=too-many-arguments
    def _tr_handler(self, thermostat_index, mode, hold, fan, current_temp,
                    heat_setpoint, cool_setpoint, humidity):
        thermostat = self.elements[thermostat_index]
        thermostat.setattr('mode', mode, False)
        thermostat.setattr('hold', hold, False)
        thermostat.setattr('fan', fan, False)
        thermostat.setattr('current_temp', current_temp, False)
        thermostat.setattr('heat_setpoint', heat_setpoint, False)
        thermostat.setattr('cool_setpoint', cool_setpoint, False)
        thermostat.setattr('humidity', humidity, True)
