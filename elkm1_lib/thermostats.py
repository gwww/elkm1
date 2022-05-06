"""Definition of an ElkM1 Thermostat"""

from __future__ import annotations

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import tr_encode, ts_encode
from .notify import Notifier


class Thermostat(Element):
    """Class representing an Thermostat"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.mode = 0
        self.hold = False
        self.fan = 0
        self.current_temp = 0
        self.heat_setpoint = 0
        self.cool_setpoint = 0
        self.humidity = 0

    def set(self, element_to_set: int, value: int) -> None:
        """(Helper) Set thermostat"""
        self._connection.send(ts_encode(self.index, value, element_to_set))


class Thermostats(Elements[Thermostat]):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Thermostat, Max.THERMOSTATS.value)
        notifier.attach("ST", self._st_handler)
        notifier.attach("TR", self._tr_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.THERMOSTAT.value)

    def _got_desc(self, descriptions: list[str | None], desc_type: int) -> None:
        super()._got_desc(descriptions, desc_type)
        # Only poll thermostats that have a name defined
        for thermostat in self.elements:
            if not thermostat.is_default_name():
                self._connection.send(tr_encode(thermostat.index))

    def _st_handler(self, group: int, device: int, temperature: int) -> None:
        if group == 2:
            self.elements[device].setattr("current_temp", temperature, True)

    def _tr_handler(
        self,
        thermostat_index: int,
        mode: int,
        hold: bool,
        fan: int,
        current_temp: int,
        heat_setpoint: int,
        cool_setpoint: int,
        humidity: int,
    ) -> None:
        thermostat = self.elements[thermostat_index]
        thermostat.setattr("mode", mode, False)
        thermostat.setattr("hold", hold, False)
        thermostat.setattr("fan", fan, False)
        thermostat.setattr("current_temp", current_temp, False)
        thermostat.setattr("heat_setpoint", heat_setpoint, False)
        thermostat.setattr("cool_setpoint", cool_setpoint, False)
        thermostat.setattr("humidity", humidity, True)
