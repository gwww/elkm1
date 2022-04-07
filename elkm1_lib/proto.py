"""Async IO."""

from __future__ import annotations

import asyncio
import logging
from functools import reduce
from collections.abc import Callable
from typing import Optional, cast

from .message import get_elk_command

LOG = logging.getLogger(__name__)


class Connection(asyncio.Protocol):  # pylint: disable=too-many-instance-attributes
    """asyncio Protocol with line parsing and queuing writes"""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        heartbeat_time: float,
        connected: Callable[[Connection], None],
        disconnected: Callable[[], None],
        got_data: Callable[[str], None],
        timeout: Callable[[str | None], None],
    ) -> None:  # pylint: disable=too-many-arguments
        self.loop = loop
        self._heartbeat_time = heartbeat_time
        self._connected_callback = connected
        self._disconnected_callback = disconnected
        self._got_data_callback = got_data
        self._timeout_callback = timeout

        self._transport: Optional[asyncio.Transport] = None
        self._waiting_for_response: Optional[str] = None
        self._write_timeout_task: Optional[asyncio.TimerHandle] = None
        self._heartbeat_timeout_task: Optional[asyncio.TimerHandle] = None
        self._queued_writes: list[tuple[str, Optional[str], float]] = []
        self._buffer = ""
        self._paused = False

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        LOG.debug("connected callback")
        self._transport = cast(asyncio.Transport, transport)
        self._connected_callback(self)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        LOG.debug("disconnected callback")
        self._transport = None
        self._cleanup()
        if self._disconnected_callback:
            self._disconnected_callback()

    def _cleanup(self) -> None:
        self._cancel_write_timer()
        self._cancel_heartbeat_timer()
        self._waiting_for_response = None
        self._queued_writes = []
        self._buffer = ""

    def close(self) -> None:
        """Stop the connection from sending/receiving/reconnecting."""
        if self._transport:
            self._transport.close()
            self._transport = None
        self._cleanup()

    def pause(self) -> None:
        """Pause the connection from sending/receiving."""
        self._cleanup()
        self._paused = True

    def resume(self) -> None:
        """Restart the connection from sending/receiving."""
        self._paused = False

    def _response_required_timeout(self) -> None:
        self._timeout_callback(self._waiting_for_response)
        self._write_timeout_task = None
        self._waiting_for_response = None
        self._process_write_queue()

    def _cancel_write_timer(self) -> None:
        if self._write_timeout_task:
            self._write_timeout_task.cancel()
            self._write_timeout_task = None

    def _cancel_heartbeat_timer(self) -> None:
        if self._heartbeat_timeout_task is not None:
            self._heartbeat_timeout_task.cancel()

    def _heartbeat_timeout(self) -> None:
        LOG.warning("ElkM1 connection heartbeat timed out, disconnecting")
        if self._transport:
            self._transport.close()

    def _restart_heartbeat_timer(self) -> None:
        self._cancel_heartbeat_timer()
        if self._heartbeat_time > 0:
            self._heartbeat_timeout_task = self.loop.call_later(
                self._heartbeat_time, self._heartbeat_timeout
            )

    def data_received(self, data: bytes) -> None:
        self._restart_heartbeat_timer()
        self._buffer += data.decode("ISO-8859-1")
        while "\r\n" in self._buffer:
            line, self._buffer = self._buffer.split("\r\n", 1)
            if get_elk_command(line) == self._waiting_for_response:
                self._waiting_for_response = None
                self._cancel_write_timer()
            self._got_data_callback(line)
        self._process_write_queue()

    def _process_write_queue(self) -> None:
        while self._queued_writes and not self._waiting_for_response:
            to_write = self._queued_writes.pop(0)
            self.write_data(to_write[0], to_write[1], timeout=to_write[2])

    def write_data(
        self,
        data: str,
        response_required: str | None = None,
        timeout: float = 5.0,
        raw: bool = False,
    ) -> None:
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
                self._write_timeout_task = self.loop.call_later(
                    timeout, self._response_required_timeout
                )

        if not raw:
            cksum = 256 - reduce(lambda x, y: x + y, map(ord, data)) % 256
            data = f"{data}{cksum:02X}"
            if int(data[0:2], 16) != len(data) - 2:
                LOG.debug("message length wrong: %s", data)

        LOG.debug("write_data '%s'", data)
        self._transport.write((data + "\r\n").encode())
