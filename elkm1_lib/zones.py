"""Definition of an ElkM1 Zone"""
from .const import (
    Max,
    TextDescriptions,
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


class Zone(Element):
    """Class representing a Zone"""

    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.definition = 0
        self.area = -1
        self.logical_status = 0
        self.physical_status = 0
        self.voltage = 0
        self.temperature = -60
        self.triggered_alarm = False

    def __str__(self):
        return (
            "{indx:d} '{name}' type:{typ} status:{logl}/{phys}"
            " area:{area:d} trig:{trig} v:{volt} temp:{temp}"
        ).format(
            name=self.name,
            indx=self._index,
            typ=ZoneType(self.definition).name,
            logl=ZoneLogicalStatus(self.logical_status).name,
            trig=self.triggered_alarm,
            volt=self.voltage,
            area=self.area,
            temp=self.temperature,
            phys=ZonePhysicalStatus(self.physical_status).name,
        )

    def bypass(self, code):
        """(Helper) Bypass zone."""
        self._elk.send(zb_encode(self._index, 0, code))

    def trigger(self):
        """(Helper) Trigger zone."""
        self._elk.send(zt_encode(self._index))

    def get_voltage(self):
        """(Helper) Get zone voltage."""
        self._elk.send(zv_encode(self._index))


class Zones(Elements):
    """Handling for multiple zones"""

    def __init__(self, elk):
        super().__init__(elk, Zone, Max.ZONES.value)
        elk.add_handler("AZ", self._az_handler)
        elk.add_handler("LW", self._lw_handler)
        elk.add_handler("ST", self._st_handler)
        elk.add_handler("ZB", self._zb_handler)
        elk.add_handler("ZC", self._zc_handler)
        elk.add_handler("ZD", self._zd_handler)
        elk.add_handler("ZP", self._zp_handler)
        elk.add_handler("ZS", self._zs_handler)
        elk.add_handler("ZV", self._zv_handler)

    def sync(self):
        """Retrieve zones from ElkM1"""
        self.elk.send(az_encode())
        self.elk.send(zd_encode())
        self.elk.send(zp_encode())
        self.elk.send(zs_encode())
        self.get_descriptions(TextDescriptions.ZONE.value)

    def _az_handler(self, alarm_status):
        for zone in self.elements:
            zone.setattr("triggered_alarm", alarm_status[zone.index] != "0", True)

    def _lw_handler(self, keypad_temps, zone_temps):  # pylint: disable=unused-argument
        for i in range(16):
            zone = self.elements[i]
            if zone_temps[zone.index] > -60:
                zone.setattr("temperature", zone_temps[zone.index], True)

    def _st_handler(self, group, device, temperature):
        if group == 0:
            self.elements[device].setattr("temperature", temperature, True)

    def _zb_handler(
        self, zone_number, zone_bypassed
    ):  # pylint: disable=unused-argument
        # If specific zone number was specified, then a ZC (zone change)
        # message will be received to update the bypass state.
        # If zone was 000 or 999 then we don't know which area was bypassed or
        # cleared and ther is no ZC. Retrieve the current zone statuses...
        if zone_number < 0 or zone_number >= Max.ZONES.value:
            self.elk.send(zs_encode())

    def _zc_handler(self, zone_number, zone_status):
        self.elements[zone_number].setattr("logical_status", zone_status[0], False)
        self.elements[zone_number].setattr("physical_status", zone_status[1], True)

    def _zd_handler(self, zone_definitions):
        for zone in self.elements:
            zone.setattr("definition", zone_definitions[zone.index], True)

    def _zp_handler(self, zone_partitions):
        for zone in self.elements:
            zone.setattr("area", zone_partitions[zone.index], True)

    def _zs_handler(self, zone_statuses):
        for zone in self.elements:
            zone.setattr("logical_status", zone_statuses[zone.index][0], False)
            zone.setattr("physical_status", zone_statuses[zone.index][1], True)

    def _zv_handler(self, zone_number, zone_voltage):
        self.elements[zone_number].setattr("voltage", zone_voltage, True)
