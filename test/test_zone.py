from unittest.mock import Mock

import pytest

from elkm1_lib.const import ZoneLogicalStatus, ZonePhysicalStatus, ZoneType
from elkm1_lib.zones import Zones

from .util import rx_msg


@pytest.fixture
def zones(notifier):
    return Zones(Mock(), notifier)


def test_zone_change(zones, notifier):
    rx_msg("ZC", "001B", notifier)
    zone = zones[0]
    assert zone.logical_status == ZoneLogicalStatus.VIOLATED
    assert zone.physical_status == ZonePhysicalStatus.SHORT


def test_bad_zone_change_length(notifier):
    with pytest.raises(ValueError):
        rx_msg("ZC", "001", notifier)


def test_zone_definition(zones, notifier):
    rx_msg("ZD", f"1111@00Q{'0' * 200}", notifier)
    assert zones[0].definition == ZoneType.BURGLAR_ENTRY_EXIT_1
    assert zones[4].definition == ZoneType.NON_ALARM
    assert zones[5].definition == ZoneType.DISABLED
    assert zones[7].definition == ZoneType.TEMPERATURE


def test_zone_alarm_state(zones, notifier):
    rx_msg("AZ", f"05:A0000{'0' * 200}", notifier)
    assert zones[0].triggered_alarm is False
    assert zones[1].triggered_alarm is True
    assert zones[2].triggered_alarm is True
    assert zones[3].triggered_alarm is True


def test_zone_voltage(zones, notifier):
    rx_msg("ZV", "123072", notifier)
    assert zones[122].voltage == pytest.approx(7.2)
