from unittest.mock import Mock

from elkm1_lib.notify import Notifier


def test_attach():
    mock_notified = Mock()
    notifier = Notifier()
    notifier.attach("foo", mock_notified)
    notifier.notify("foo", {"something": 42})
    mock_notified.assert_called_once_with(something=42)


def test_attach_multiple():
    mock_notified1 = Mock()
    mock_notified2 = Mock()
    notifier = Notifier()
    notifier.attach("foo", mock_notified1)
    notifier.attach("foo", mock_notified2)
    notifier.notify("foo", {"something": 42})
    mock_notified1.assert_called_once_with(something=42)
    mock_notified2.assert_called_once_with(something=42)


def test_attach_same_twice_doesnt_call_twice():
    mock_notified = Mock()
    notifier = Notifier()
    notifier.attach("foo", mock_notified)
    notifier.attach("foo", mock_notified)
    notifier.notify("foo", {"something": 42})
    mock_notified.assert_called_once_with(something=42)


def test_deattach():
    mock_notified1 = Mock()
    mock_notified2 = Mock()
    notifier = Notifier()
    notifier.attach("foo", mock_notified1)
    notifier.attach("foo", mock_notified2)
    notifier.detach("foo", mock_notified1)
    notifier.notify("foo", {"something": 42})
    mock_notified1.assert_not_called()
    mock_notified2.assert_called_once_with(something=42)
