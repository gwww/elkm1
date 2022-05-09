import pytest

from elkm1_lib.notify import Notifier


@pytest.fixture
def notifier():
    return Notifier()
