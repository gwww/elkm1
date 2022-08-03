"""Async IO."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from functools import partial, reduce
from typing import Optional, cast

import serial_asyncio

from .message import MessageEncode, decode, get_elk_command
from .notify import Notifier
from .util import parse_url

LOG = logging.getLogger(__name__)


class Connection:
    """Method to manage a connection to the ElkM1."""

    def __init__(
        self,
        url: str,
        notifier: Notifier,
        loop: asyncio.AbstractEventLoop | None = None,
    ):
        """Setup a connection."""
        self._url = url
        self._notifier = notifier
        self._loop = loop if loop else asyncio.get_event_loop()

        self._elk_protocol: _ElkProtocol | None = None
        self._connection_retry_time = 1
        self._reconnect_task: asyncio.TimerHandle | None = None

    async def connect(self) -> None:
        """Asyncio connection to Elk."""

        LOG.info("Connecting to ElkM1 at %s", self._url)
        scheme, dest, param, ssl_context = parse_url(self._url)
        heartbeat_time = 120 if scheme != "serial" else -1

        connection = partial(
            _ElkProtocol,
            self._loop,
            heartbeat_time,
            self._connected_callback,
            self._disconnected_callback,
            self._got_data_callback,
            self._timeout_callback,
        )
        try:
            if scheme == "serial":
                await serial_asyncio.create_serial_connection(
                    self._loop, connection, dest, baudrate=param
                )
            else:
                await asyncio.wait_for(
                    self._loop.create_connection(
                        connection, host=dest, port=param, ssl=ssl_context
                    ),
                    timeout=30,
                )
        except (ValueError, OSError, asyncio.TimeoutError) as err:
            if self._connection_retry_time <= 0:
                return

            LOG.warning(
                "Could not connect to ElkM1 (%s). Retrying in %d seconds",
                err,
                self._connection_retry_time,
            )
            self._start_connection_retry_timer()

    def is_connected(self) -> bool:
        """Is the connection active?"""
        return self._elk_protocol is not None

    def send(self, msg: MessageEncode) -> None:
        """Send a message on the connection."""
        if self._elk_protocol:
            self._elk_protocol.write_data(msg.message, msg.response_command)

    def send_raw(self, msg: str) -> None:
        """Send a message on the connection."""
        if self._elk_protocol:
            self._elk_protocol.write_data(msg, raw=True)

    def pause(self) -> None:
        """Pause the connection from sending/receiving."""
        if self._elk_protocol:
            self._elk_protocol.pause()

    def resume(self) -> None:
        """Restart the connection from sending/receiving."""
        if self._elk_protocol:
            self._elk_protocol.resume()

    def disconnect(self) -> None:
        """Disconnect the connection from sending/receiving."""
        self._connection_retry_time = -1  # Stop future timeout reconnects
        if self._elk_protocol is not None:
            self._elk_protocol.close()
            self._elk_protocol = None
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    def _start_connection_retry_timer(self) -> None:
        timeout = self._connection_retry_time
        if timeout > 0:
            self._reconnect_task = self._loop.call_later(timeout, self._reconnect)
            self._connection_retry_time = min(60, timeout * 2)

    def _connected_callback(self, elk_protocol: _ElkProtocol) -> None:
        """Login and sync the ElkM1 panel to memory."""
        LOG.info("Connected to ElkM1")
        self._elk_protocol = elk_protocol
        self._connection_retry_time = 1
        self._notifier.notify("connected", {})

    def _reconnect(self) -> None:
        asyncio.ensure_future(self.connect())

    def _disconnected_callback(self) -> None:
        LOG.warning("ElkM1 at %s disconnected", self._url)
        self._elk_protocol = None
        self._start_connection_retry_timer()
        self._notifier.notify("disconnected", {})

    def _got_data_callback(self, data: str) -> None:
        LOG.debug("got_data '%s'", data)
        try:
            decoded = decode(data)
            if decoded:
                self._notifier.notify(decoded[0], decoded[1])
        except (ValueError, AttributeError) as exc:
            LOG.error("Invalid message '%s'", data, exc_info=exc)

    def _timeout_callback(self, msg_code: str) -> None:
        self._notifier.notify("timeout", {"msg_code": msg_code})


class _ElkProtocol(asyncio.Protocol):
    """asyncio Protocol with line parsing and queuing writes"""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        heartbeat_time: float,
        connected: Callable[[_ElkProtocol], None],
        disconnected: Callable[[], None],
        got_data: Callable[[str], None],
        timeout: Callable[[str | None], None],
    ) -> None:
        self._loop = loop
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
        if exc:
            LOG.exception(exc)
        exc_str = f" (exception: {exc.__class__.__name__})" if exc is not None else ""
        LOG.debug("disconnected callback%s", exc_str)
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
            self._heartbeat_timeout_task = self._loop.call_later(
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
                self._write_timeout_task = self._loop.call_later(
                    timeout, self._response_required_timeout
                )

        if not raw:
            cksum = (256 - reduce(lambda x, y: x + y, map(ord, data))) % 256
            data = f"{data}{cksum:02X}"
            if int(data[0:2], 16) != len(data) - 2:
                LOG.debug("message length wrong: %s", data)

        LOG.debug("write_data '%s'", data)
        self._transport.write((data + "\r\n").encode())
