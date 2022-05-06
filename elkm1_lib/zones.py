"""Definition of an ElkM1 Zone"""

from .connection import Connection
from .const import (
    Max,
    TextDescriptions,
    ZoneAlarmState,
    ZoneLogicalStatus,
    ZonePhysicalStatus,
    ZoneType,
)
from .elements import Element, Elements
from .message import (
    az_encode,
    zb_encode,
    zd_encode,
    zp_encode,
    zs_encode,
    zt_encode,
    zv_encode,
)
from .notify import Notifier


class Zone(Element):
    """Class representing a Zone"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.definition = ZoneType.DISABLED
        self.logical_status = ZoneLogicalStatus.NORMAL
        self.physical_status = ZonePhysicalStatus.UNCONFIGURED
        self.area = -1
        self.voltage = 0
        self.temperature = -60
        self.triggered_alarm = False

    def __str__(self) -> str:
        return (
            f"{self._index} '{self.name}' type:{ZoneType(self.definition).name} status:"
            f"{ZoneLogicalStatus(self.logical_status).name}/"
            f"{ZonePhysicalStatus(self.physical_status).name} "
            f"area:{self.area} trig:{self.triggered_alarm} "
            f"volt:{self.voltage} temp:{self.temperature}"
        )

    def bypass(self, code: int) -> None:
        """(Helper) Bypass zone."""
        self._connection.send(zb_encode(self._index, 0, code))

    def trigger(self) -> None:
        """(Helper) Trigger zone."""
        self._connection.send(zt_encode(self._index))

    def get_voltage(self) -> None:
        """(Helper) Get zone voltage."""
        self._connection.send(zv_encode(self._index))


class Zones(Elements[Zone]):
    """Handling for multiple zones"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Zone, Max.ZONES.value)
        notifier.attach("AZ", self._az_handler)
        notifier.attach("LW", self._lw_handler)
        notifier.attach("ST", self._st_handler)
        notifier.attach("ZB", self._zb_handler)
        notifier.attach("ZC", self._zc_handler)
        notifier.attach("ZD", self._zd_handler)
        notifier.attach("ZP", self._zp_handler)
        notifier.attach("ZS", self._zs_handler)
        notifier.attach("ZV", self._zv_handler)

    def sync(self) -> None:
        """Retrieve zones from ElkM1"""
        self._connection.send(az_encode())
        self._connection.send(zd_encode())
        self._connection.send(zp_encode())
        self._connection.send(zs_encode())
        self.get_descriptions(TextDescriptions.ZONE.value)

    def _az_handler(self, alarm_status: list[ZoneAlarmState]) -> None:
        for zone in self.elements:
            zone.setattr(
                "triggered_alarm",
                alarm_status[zone.index] != ZoneAlarmState.NO_ALARM,
                True,
            )

    def _lw_handler(self, keypad_temps: list[int], zone_temps: list[int]) -> None:
        for i in range(16):
            zone = self.elements[i]
            if zone_temps[zone.index] > -60:
                zone.setattr("temperature", zone_temps[zone.index], True)

    def _st_handler(self, group: int, device: int, temperature: int) -> None:
        if group == 0:
            self.elements[device].setattr("temperature", temperature, True)

    def _zb_handler(self, zone_number: int, zone_bypassed: bool) -> None:
        # If specific zone number was specified, then a ZC (zone change)
        # message will be received to update the bypass state.
        # If zone was 000 or 999 then we don't know which area was bypassed or
        # cleared and there is no ZC. Retrieve the current zone statuses...
        if zone_number < 0 or zone_number >= Max.ZONES.value:
            self._connection.send(zs_encode())

    def _zc_handler(
        self,
        zone_number: int,
        zone_status: tuple[ZoneLogicalStatus, ZonePhysicalStatus],
    ) -> None:
        self.elements[zone_number].setattr("logical_status", zone_status[0], False)
        self.elements[zone_number].setattr("physical_status", zone_status[1], True)

    def _zd_handler(self, zone_definitions: list[ZoneType]) -> None:
        for zone in self.elements:
            zone.setattr("definition", zone_definitions[zone.index], True)

    def _zp_handler(self, zone_partitions: list[int]) -> None:
        for zone in self.elements:
            zone.setattr("area", zone_partitions[zone.index], True)

    def _zs_handler(
        self, zone_statuses: list[tuple[ZoneLogicalStatus, ZonePhysicalStatus]]
    ) -> None:
        for zone in self.elements:
            zone.setattr("logical_status", zone_statuses[zone.index][0], False)
            zone.setattr("physical_status", zone_statuses[zone.index][1], True)

    def _zv_handler(self, zone_number: int, zone_voltage: float) -> None:
        self.elements[zone_number].setattr("voltage", zone_voltage, True)
