from unittest.mock import Mock

import pytest

from elkm1_lib.areas import Area, Areas
from elkm1_lib.const import AlarmState, ArmedStatus, ArmUpState
from elkm1_lib.message import MessageEncode

from .util import rx_msg


@pytest.fixture
def areas(notifier):
    return Areas(Mock(), notifier)


def test_entry_exit_general(areas, notifier):
    rx_msg("EE", "100601201", notifier)
    area = areas[0]
    assert area.is_exit is True
    assert area.timer1 == 60
    assert area.timer2 == 120
    assert area.armed_status == ArmedStatus.ARMED_AWAY


def test_entry_exit_armed_status(areas, notifier):
    area = areas[0]
    assert area.is_armed() is False
    rx_msg("EE", "110300601", notifier)
    assert area.is_armed() is True


def test_alarm_memory(areas, notifier):
    rx_msg("AM", "10101010", notifier, zeros="")
    assert areas[0].alarm_memory is True
    assert areas[1].alarm_memory is False


def test_armed_status(areas, notifier):
    rx_msg("AS", "100000004000000030000000", notifier)
    area = areas[0]
    assert area.armed_status == ArmedStatus.ARMED_AWAY
    assert area.arm_up_state == ArmUpState.FULLY_ARMED
    assert area.alarm_state == AlarmState.FIRE_ALARM


def test_armed_status_updates_alarm_triggers(notifier):
    mock_connection = Mock()
    Areas(mock_connection, notifier)
    rx_msg("AS", "100000004000000030000000", notifier)
    mock_connection.send.assert_called_with(
        MessageEncode(message="06az00", response_command="AZ")
    )


def test_is_in_alarm_state():
    area = Area(0, Mock(), Mock())
    assert area.in_alarm_state() is False

    area.alarm_state = AlarmState.POLICE_ALARM
    assert area.in_alarm_state() is True
