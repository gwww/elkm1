"""Async IO."""

import asyncio
from functools import reduce
import logging

from .message import get_elk_command, timeout_decode

LOG = logging.getLogger(__name__)


class Connection(asyncio.Protocol):
    """asyncio Protocol with line parsing and queuing writes"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, loop, connected, disconnected, got_data):
        self.loop = loop
        self._connected_callback = connected
        self._disconnected_callback = disconnected
        self._got_data_callback = got_data

        self._transport = None
        self._waiting_for_response = None
        self._timeout_task = None
        self._queued_writes = []
        self._buffer = ''
        self._paused = False

    def connection_made(self, transport):
        LOG.debug("connected callback")
        self._transport = transport
        self._connected_callback(transport, self)

    def connection_lost(self, exc):
        LOG.debug("disconnected callback")
        self._transport = None
        self._cleanup()
        self._disconnected_callback()

    def _cleanup(self):
        self._cancel_timer()
        self._waiting_for_response = None
        self._queued_writes = []
        self._buffer = ''

    def pause(self):
        """Pause the connection from sending/receiving."""
        self._cleanup()
        self._paused = True

    def resume(self):
        """Restart the connection from sending/receiving."""
        self._paused = False

    def _response_required_timeout(self):
        timeout_decode(self._waiting_for_response)
        self._timeout_task = None
        self._waiting_for_response = None
        self._process_write_queue()

    def _cancel_timer(self):
        if self._timeout_task:
            self._timeout_task.cancel()
            self._timeout_task = None

    def data_received(self, data):
        self._buffer += data.decode('ISO-8859-1')
        while "\r\n" in self._buffer:
            line, self._buffer = self._buffer.split("\r\n", 1)
            if get_elk_command(line) == self._waiting_for_response:
                self._waiting_for_response = None
                self._cancel_timer()
            self._got_data_callback(line)
        self._process_write_queue()

    def _process_write_queue(self):
        while self._queued_writes and not self._waiting_for_response:
            to_write = self._queued_writes.pop(0)
            self.write_data(to_write[0], to_write[1], timeout=to_write[2])

    def write_data(self, data, response_required=None, timeout=5.0, raw=False):
        """Write data on the asyncio Protocol"""
        if self._transport is None:
            return

        if self._paused:
            return

        if self._waiting_for_response:
            LOG.debug("queueing write %s", data)
            self._queued_writes.append((data, response_required, timeout))
            return

        if response_required:
            self._waiting_for_response = response_required
            if timeout > 0:
                self._timeout_task = self.loop.call_later(
                    timeout, self._response_required_timeout)

        if not raw:
            cksum = 256 - reduce(lambda x, y: x+y, map(ord, data)) % 256
            data = data + '{:02X}'.format(cksum)
            if int(data[0:2], 16) != len(data)-2:
                LOG.debug("message length wrong: %s", data)

        LOG.debug("write_data '%s'", data)
        self._transport.write((data + '\r\n').encode())
