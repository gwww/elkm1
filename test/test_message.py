import datetime as dt
from unittest.mock import Mock

import pytest

import elkm1_lib.message as m


def test_housecode_to_index_accepts_valid_codes():
    assert m.housecode_to_index("A01") == 0
    assert m.housecode_to_index("P16") == 255
    assert m.housecode_to_index("f6") == 85


def test_housecode_to_index_raises_error_on_invalid():
    with pytest.raises(ValueError):
        m.housecode_to_index("asdf")
    with pytest.raises(ValueError):
        m.housecode_to_index("Q01")
    with pytest.raises(ValueError):
        m.housecode_to_index("A00")
    with pytest.raises(ValueError):
        m.housecode_to_index("A17")


def test_index_to_housecode_accepts_valid_indices():
    assert m.index_to_housecode(0) == "A01"
    assert m.index_to_housecode(10) == "A11"
    assert m.index_to_housecode(16) == "B01"
    assert m.index_to_housecode(255) == "P16"


def test_index_to_housecode_raises_error_on_invalid():
    with pytest.raises(ValueError):
        m.index_to_housecode(-1)
    with pytest.raises(ValueError):
        m.index_to_housecode(256)


def test_decode_raises_value_error_on_bad_message():
    decoder = m.MessageDecode()
    with pytest.raises(ValueError):
        decoder.decode("a really really bad message")


def test_decode_calls_unknown_handler_on_bad_command_or_not_implemented():
    mock_unknown_handler = Mock()
    decoder = m.MessageDecode()
    decoder.add_handler("unknown", mock_unknown_handler)
    decoder.decode("08XXtest28")
    mock_unknown_handler.assert_called_once_with(msg_code="XX", data="test")


def test_decode_raises_value_error_on_length_too_long():
    decoder = m.MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("42CV01000990030")
    assert str(excinfo.value) == "Incorrect message length"


def test_decode_raises_value_error_on_length_too_short():
    decoder = m.MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("02CV01000990030")
    assert str(excinfo.value) == "Incorrect message length"


def test_decode_raises_value_error_on_bad_checksum():
    decoder = m.MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("0DCV01000990042")
    assert str(excinfo.value) == "Bad checksum"


def test_decode_raises_value_error_on_short_message():
    decoder = m.MessageDecode()
    with pytest.raises(ValueError) as excinfo:
        decoder.decode("")
    assert str(excinfo.value) == "Message invalid"


def test_decode_login_success():
    mock_login_success_handler = Mock()
    decoder = m.MessageDecode()
    decoder.add_handler("login_success", mock_login_success_handler)
    decoder.decode("Login successful")
    mock_login_success_handler.assert_called_once_with()


def test_decode_login_failed():
    mock_login_failed_handler = Mock()
    decoder = m.MessageDecode()
    decoder.add_handler("login_failed", mock_login_failed_handler)
    decoder.decode("Username/Password not found")
    mock_login_failed_handler.assert_called_once_with()


def test_encode_message_with_a_variable():
    assert m.ps_encode(1) == ("07ps100", "PS")


def test_al_encode():
    assert m.al_encode(4, 2, 4242) == ("0Da4300424200", "AS")


def test_cf_encode():
    assert m.cf_encode(42) == ("09cf04300", None)


def test_ct_encode():
    assert m.ct_encode(42) == ("09ct04300", None)


def test_cn_encode():
    assert m.cn_encode(42, 4242) == ("0Ecn0430424200", None)


def test_cr_encode():
    assert m.cr_encode(42) == ("08cr4300", "CR")


def test_cw_encode():
    assert m.cw_encode(5, (21, 40), 2) == ("0Dcw060541600", None)


def test_cv_encode():
    assert m.cv_encode(12) == ("08cv1300", "CV")


def test_cx_encode():
    assert m.cx_encode(10, 54321) == ("0Dcx115432100", "CV")


def test_dm_encode():
    assert m.dm_encode(4, 1, 0, 42, "Hello", "  World") == (
        "2Edm51000042Hello^^^^^^^^^^^  World^^^^^^^^^00",
        None,
    )


def test_dm_encode_too_long_is_truncated():
    assert m.dm_encode(4, 1, 0, 42, "Hello this is a long message", "  World") == (
        "2Edm51000042Hello this is a   World^^^^^^^^^00",
        None,
    )


def test_pc_encode():
    assert m.pc_encode(10, 29, 38, 1234) == ("11pcA112938123400", None)


def test_pf_encode():
    assert m.pf_encode(10) == ("09pfA1100", None)


def test_pn_encode():
    assert m.pn_encode(10) == ("09pnA1100", None)


def test_ps_encode():
    assert m.ps_encode(2) == ("07ps200", "PS")


def test_pt_encode():
    assert m.pt_encode(10) == ("09ptA1100", None)


def test_sd_encode():
    assert m.sd_encode(10, 42) == ("0Bsd1004300", "SD")


def test_sp_encode():
    assert m.sp_encode(242) == ("09sp24200", None)


def test_sw_encode():
    assert m.sw_encode(424) == ("09sw42400", None)


def test_rw_encode():
    assert m.rw_encode(dt.datetime(2020, 10, 19, 11, 47, 27, 942490)) == (
        "13rw274711219102000",
        None,
    )


def test_tn_encode():
    assert m.tn_encode(142) == ("09tn14300", None)


def test_tr_encode():
    assert m.tr_encode(6) == ("08tr0700", None)


def test_ts_encode():
    assert m.ts_encode(6, 7, 42) == ("0Bts07074200", None)


def test_zb_encode():
    assert m.zb_encode(142, 7, 123456) == ("10zb143812345600", "ZB")


def test_zt_encode():
    assert m.zt_encode(199) == ("09zt20000", None)


def test_zv_encode():
    assert m.zv_encode(200) == ("09zv20100", "ZV")


def test_ua_encode():
    assert m.ua_encode(654321) == ("0Cua65432100", "UA")
