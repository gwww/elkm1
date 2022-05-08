from unittest.mock import Mock

import pytest

from elkm1_lib.const import SettingFormat
from elkm1_lib.message import MessageEncode
from elkm1_lib.settings import Setting, Settings

from .util import rx_msg


@pytest.fixture
def settings(notifier):
    return Settings(Mock(), notifier)


def test_settings_number(settings, notifier):
    rx_msg("CR", "01001230", notifier)
    setting = settings[0]
    assert setting.value_format == SettingFormat.NUMBER
    assert setting.value == 123


def test_settings_time_of_day(settings, notifier):
    rx_msg("CR", "01054162", notifier)
    setting = settings[0]
    assert setting.value_format == SettingFormat.TIME_OF_DAY
    assert setting.value == (21, 40)


def test_setting_set_types_are_correct():
    setting = Setting(0, Mock(), Mock())

    setting.value_format = SettingFormat.NUMBER
    with pytest.raises(ValueError):
        setting.set((1, 2))

    setting.value_format = SettingFormat.TIME_OF_DAY
    with pytest.raises(ValueError):
        setting.set(42)


def test_setting_write_new_value_called():
    mock = Mock()
    setting = Setting(0, mock, Mock())

    setting.value_format = SettingFormat.NUMBER
    setting.set(42)
    mock.send.assert_called_with(
        MessageEncode(message="0Dcw010004200", response_command=None)
    )

    setting.value_format = SettingFormat.TIME_OF_DAY
    setting.set((21, 40))
    mock.send.assert_called_with(
        MessageEncode(message="0Dcw010541600", response_command=None)
    )
