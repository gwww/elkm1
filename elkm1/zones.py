"""Definition of an ElkM1 Zone"""
from .const import Max, TextDescriptions, ZoneType, \
                   ZoneLogicalStatus, ZonePhysicalStatus
from .elements import Element, Elements
from .message import add_message_handler, zd_encode, zp_encode, zs_encode


class Zone(Element):
    """Class representing a Zone"""
    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.definition = 0
        self.area = 0
        self.bypassed = False
        self.logical_status = 0
        self.physical_status = 0
        self.voltage = None
        self.temperature = None

    def __str__(self):
        return ("{indx:d} '{name}' type:{typ} status:{logl}/{phys}"
                " area:{area:d} v:{volt} temp:{temp}").format(
                    name=self.name, indx=self._index,
                    typ=ZoneType(self.definition).name,
                    logl=ZoneLogicalStatus(self.logical_status).name,
                    volt=self.voltage, area=self.area, temp=self.temperature,
                    phys=ZonePhysicalStatus(self.physical_status).name)

class Zones(Elements):
    """Handling for multiple zones"""
    def __init__(self, elk):
        super().__init__(elk, Zone, Max.ZONES.value)
        add_message_handler('LW', self._lw_handler)
        add_message_handler('ZB', self._zb_handler)
        add_message_handler('ZC', self._zc_handler)
        add_message_handler('ZD', self._zd_handler)
        add_message_handler('ZP', self._zp_handler)
        add_message_handler('ZS', self._zs_handler)
        add_message_handler('ZV', self._zv_handler)

    def sync(self):
        """Retrieve zones from ElkM1"""
        self.elk.send(zd_encode())
        self.elk.send(zp_encode())
        self.elk.send(zs_encode())
        self.get_descriptions(TextDescriptions.ZONE.value)

    # pylint: disable=unused-argument
    def _lw_handler(self, keypad_temps, zone_temps):
        for i in range(16):
            zone = self.elements[i]
            if zone_temps[zone.index] > -60:
                zone.setattr('temperature', zone_temps[zone.index])

    def _zb_handler(self, zone_number, zone_bypassed):
        self.elements[zone_number].setattr('bypassed', zone_bypassed)

    def _zc_handler(self, zone_number, zone_status):
        self.elements[zone_number].setattr('logical_status', zone_status[0])
        self.elements[zone_number].setattr('physical_status', zone_status[1])

    def _zd_handler(self, zone_definitions):
        for zone in self.elements:
            zone.setattr('definition', zone_definitions[zone.index])

    def _zp_handler(self, zone_partitions):
        for zone in self.elements:
            zone.setattr('area', zone_partitions[zone.index])

    def _zs_handler(self, zone_statuses):
        for zone in self.elements:
            zone.setattr('logical_status', zone_statuses[zone.index][0])
            zone.setattr('physical_status', zone_statuses[zone.index][1])

    def _zv_handler(self, zone_number, zone_voltage):
        self.elements[zone_number].setattr('voltage', zone_voltage)
