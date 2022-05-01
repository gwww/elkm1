import pytest

from elkm1_lib.util import parse_url, pretty_const


def test_parse_url_valid_non_ssl_socket():
    (scheme, host, port, ssl) = parse_url("elk://some.host:1234")
    assert scheme == "elk"
    assert host == "some.host"
    assert port == 1234
    assert ssl is None


def test_parse_url_valid_ssl_socket():
    (scheme, host, port, ssl) = parse_url("elks://another.host:5678")
    assert scheme == "elks"
    assert host == "another.host"
    assert port == 5678
    assert ssl is not None


def test_parse_url_default_non_ssl_port():
    (scheme, host, port, ssl) = parse_url("elk://192.168.0.123")
    assert scheme == "elk"
    assert host == "192.168.0.123"
    assert port == 2101
    assert ssl is None


def test_parse_url_default_ssl_port():
    (scheme, host, port, ssl) = parse_url("elks://ssl.host")
    assert scheme == "elks"
    assert host == "ssl.host"
    assert port == 2601
    assert ssl is not None


def test_parse_url_serial_non_implemented():
    (scheme, host, port, ssl) = parse_url("serial:///dev/tty:4800")
    assert scheme == "serial"
    assert host == "/dev/tty"
    assert port == 4800
    assert ssl is None


def test_parse_url_unknown_scheme():
    with pytest.raises(ValueError):
        parse_url("bad_scheme://rest")


def test_pretty_const_with_single_word():
    rsp = pretty_const("TESTING")
    assert rsp == "Testing"


def test_pretty_const_with_two_words():
    rsp = pretty_const("FIRE_ALARM")
    assert rsp == "Fire alarm"
