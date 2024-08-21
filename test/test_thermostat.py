from unittest.mock import Mock

import pytest

from elkm1_lib.const import ThermostatFan, ThermostatMode, ThermostatSetting
from elkm1_lib.message import MessageEncode
from elkm1_lib.thermostats import Thermostat, Thermostats

from .util import rx_msg


@pytest.fixture
def thermostats(notifier):
    return Thermostats(Mock(), notifier)


def test_entry_exit_general(thermostats, notifier):
    rx_msg("TR", "0120072687500", notifier)
    thermostat = thermostats[0]
    assert thermostat.mode == ThermostatMode.COOL
    assert thermostat.hold is False
    assert thermostat.fan == ThermostatFan.AUTO
    assert thermostat.current_temp == 72
    assert thermostat.heat_setpoint == 68
    assert thermostat.cool_setpoint == 75
    assert thermostat.humidity == 0


def test_thermostat_set_types_are_correct(notifier):
    thermostat = Thermostat(0, Mock(), notifier)

    with pytest.raises(ValueError):
        thermostat.set(ThermostatSetting.MODE, 3)
    with pytest.raises(ValueError):
        thermostat.set(ThermostatSetting.COOL_SETPOINT, True)


def test_thermostat_set_sends_correct_command_to_elk():
    mock = Mock()
    thermostat = Thermostat(0, mock, Mock())

    thermostat.set(ThermostatSetting.MODE, ThermostatMode.COOL)
    mock.send.assert_called_with(
        MessageEncode(message="0Bts0102000", response_command=None)
    )

    thermostat.set(ThermostatSetting.HOLD, True)
    mock.send.assert_called_with(
        MessageEncode(message="0Bts0101100", response_command=None)
    )

    thermostat.set(ThermostatSetting.FAN, ThermostatFan.AUTO)
    mock.send.assert_called_with(
        MessageEncode(message="0Bts0100200", response_command=None)
    )

    thermostat.set(ThermostatSetting.HEAT_SETPOINT, 42)
    mock.send.assert_called_with(
        MessageEncode(message="0Bts0142500", response_command=None)
    )
