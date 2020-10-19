from unittest.mock import Mock

import pytest

from elkm1_lib.message import (MessageDecode, MessageEncode,
                               housecode_to_index, index_to_housecode,
                               ps_encode)


def test_housecode_to_index_accepts_valid_codes():
    assert housecode_to_index("A01") == 0
    assert housecode_to_index("P16") == 255
    assert housecode_to_index("f6") == 85


def test_housecode_to_index_raises_error_on_invalid():
    with pytest.raises(ValueError):
        housecode_to_index("asdf")
    with pytest.raises(ValueError):
        housecode_to_index("Q01")
    with pytest.raises(ValueError):
        housecode_to_index("A00")
    with pytest.raises(ValueError):
        housecode_to_index("A17")


def test_index_to_housecode_accepts_valid_indices():
    assert index_to_housecode(0) == "A01"
    assert index_to_housecode(16) == "B01"
    assert index_to_housecode(255) == "P16"


def test_index_to_housecode_raises_error_on_invalid():
    with pytest.raises(ValueError):
        index_to_housecode(-1)
    with pytest.raises(ValueError):
        index_to_housecode(256)


def test_decode_raises_value_error_on_bad_message():
    decoder = MessageDecode()
    with pytest.raises(ValueError):
        decoder.decode("a really really bad message")


def test_decode_calls_unknown_handler_on_bad_command_or_not_implemented():
    mock_unknown_handler = Mock()
    decoder = MessageDecode()
    decoder.add_handler("unknown", mock_unknown_handler)
    decoder.decode("08XXtest28")
    mock_unknown_handler.assert_called_once_with(msg_code="XX", data="test")


def test_decode_raises_value_error_on_length_too_long():
    decoder = MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("42CV01000990030")
    assert str(excinfo.value) == "Elk message length incorrect"


def test_decode_raises_value_error_on_length_too_short():
    decoder = MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("02CV01000990030")
    assert str(excinfo.value) == "Elk message length incorrect"


def test_decode_raises_value_error_on_bad_checksum():
    decoder = MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("0DCV01000990042")
    assert str(excinfo.value) == "Elk message checksum invalid"


def test_encode_message_with_a_variable():
    assert ps_encode(1) == ("07ps100", "PS")
