from unittest.mock import Mock

import pytest

from elkm1_lib.areas import Areas
from elkm1_lib.const import AlarmState, ArmedStatus, ArmLevel, ArmUpState
from elkm1_lib.message import MessageEncode

from .util import rx_msg


@pytest.fixture
def areas(notifier):
    return Areas(Mock(), notifier)


def test_entry_exit_general(areas, notifier):
    rx_msg("EE", "100601201", notifier)
    area = areas[0]
    assert area.is_exit == True
    assert area.timer1 == 60
    assert area.timer2 == 120
    assert area.armed_status == ArmedStatus.ARMED_AWAY


def test_entry_exit_armed_status(areas, notifier):
    area = areas[0]
    assert area.is_armed() == False
    rx_msg("EE", "110300601", notifier)
    assert area.is_armed() == True


def test_alarm_memory(areas, notifier):
    rx_msg("AM", "10101010", notifier, zeros="")
    assert areas[0].alarm_memory == True
    assert areas[1].alarm_memory == False


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


def test_armed_status_does_not_update_alarm_triggers(notifier):
    mock_connection = Mock()
    Areas(mock_connection, notifier)
    rx_msg("AS", "000000001000000000000000", notifier)
    mock_connection.send.assert_not_called()
