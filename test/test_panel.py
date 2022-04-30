from unittest.mock import Mock, call

import pytest

from elkm1_lib.panel import Panel


def test_system_trouble_status_no_trouble():
    mock_connection = Mock()
    mock_notify = Mock()
    panel = Panel(mock_connection, mock_notify)
    panel._ss_handler("0000000000000000000000000000000000")
    assert panel.system_trouble_status == ""


def test_system_trouble_status_boolean_status():
    mock_connection = Mock()
    mock_notify = Mock()
    panel = Panel(mock_connection, mock_notify)
    panel._ss_handler("1000000000000000000000000000000000")
    assert panel.system_trouble_status == "AC Fail"


def test_system_trouble_status_zone_trouble():
    mock_connection = Mock()
    mock_notify = Mock()
    panel = Panel(mock_connection, mock_notify)
    panel._ss_handler("0900000000000000000000000000000000")
    assert panel.system_trouble_status == "Box Tamper zone 9"


def test_system_trouble_status_last_trouble():
    mock_connection = Mock()
    mock_notify = Mock()
    panel = Panel(mock_connection, mock_notify)
    panel._ss_handler("0000000000000000000000000000000005")
    assert panel.system_trouble_status == "Fire zone 5"


def test_system_trouble_status_multiple_troubles():
    mock_connection = Mock()
    mock_notify = Mock()
    panel = Panel(mock_connection, mock_notify)
    panel._ss_handler("1700100000000000000000000000000000")
    assert (
        panel.system_trouble_status == "AC Fail, Box Tamper zone 7, Low Battery Control"
    )
