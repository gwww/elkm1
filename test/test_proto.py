import pytest
from unittest.mock import Mock, call
from elkm1_lib.proto import Connection

def test_receive_single_packet_and_pass_to_handler():
    mock_gotdata = Mock()
    connection = Connection(None, None, None, mock_gotdata)
    connection.data_received('test\r\n'.encode())
    mock_gotdata.assert_called_once_with('test')

def test_receive_multiple_packets():
    mock_gotdata = Mock()
    connection = Connection(None, None, None, mock_gotdata)
    connection.data_received('test1\r\ntest2\r\n'.encode())
    mock_gotdata.assert_has_calls([call('test1'), call('test2')])

def test_received_full_packet_and_partial_packet():
    mock_gotdata = Mock()
    connection = Connection(None, None, None, mock_gotdata)
    connection.data_received('test1\r\nfirst-bit,'.encode())
    mock_gotdata.assert_called_once_with('test1')

    connection.data_received('second-bit\r\n'.encode())
    mock_gotdata.assert_has_calls([call('test1'), call('first-bit,second-bit')])

def test_write_simple():
    connection = Connection(None, None, None, None)
    connection._transport = Mock()
    connection.write_data('08cv0900')
    connection._transport.write.assert_called_once_with('08cv0900F6\r\n'.encode())
