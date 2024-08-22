"""Definition of an ElkM1 Thermostat"""

from __future__ import annotations

from .connection import Connection
from .const import (
    Max,
    TextDescriptions,
    ThermostatFan,
    ThermostatMode,
    ThermostatSetting,
)
from .elements import Element, Elements
from .message import tr_encode, ts_encode
from .notify import Notifier

SETTING_TYPING = {
    ThermostatSetting.MODE: ThermostatMode,
    ThermostatSetting.HOLD: bool,
    ThermostatSetting.FAN: ThermostatFan,
    ThermostatSetting.GET_TEMPERATURE: int,
    ThermostatSetting.COOL_SETPOINT: int,
    ThermostatSetting.HEAT_SETPOINT: int,
}


class Thermostat(Element):
    """Class representing an Thermostat"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.mode: ThermostatMode | None = None
        self.hold = False
        self.fan: ThermostatFan | None = None
        self.current_temp = 0
        self.heat_setpoint = 0
        self.cool_setpoint = 0
        self.humidity = 0

    def set(
        self,
        element_to_set: ThermostatSetting,
        val: bool | int | ThermostatMode | ThermostatFan,
    ) -> None:
        """(Helper) Set thermostat"""
        if (  # pylint: disable=unidiomatic-typecheck
            type(val) is not SETTING_TYPING[element_to_set]
        ):
            raise ValueError("Wrong type for thermostat setting.")
        if isinstance(val, bool):
            setting = 1 if val else 0
        elif isinstance(val, ThermostatFan | ThermostatMode):
            setting = val.value
        else:
            setting = val

        self._connection.send(ts_encode(self.index, setting, element_to_set))

    def _configured_was_set(self) -> None:
        self._connection.send(tr_encode(self.index), priority_send=True)


class Thermostats(Elements[Thermostat]):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Thermostat, Max.THERMOSTATS.value)
        notifier.attach("ST", self._st_handler)
        notifier.attach("TR", self._tr_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self.get_descriptions(TextDescriptions.THERMOSTAT.value)

    def _st_handler(self, group: int, device: int, temperature: int) -> None:
        if group == 2:
            self.elements[device].setattr("current_temp", temperature, True)

    def _tr_handler(
        self,
        thermostat_index: int,
        mode: ThermostatMode,
        hold: bool,
        fan: ThermostatFan,
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
