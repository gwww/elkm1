"""Manage connection and IO to Elk."""

from __future__ import annotations

import asyncio
from collections import deque
from functools import reduce
import logging
from typing import NamedTuple, Optional

import async_timeout
import serial_asyncio

from .message import MessageEncode, decode, get_elk_command
from .notify import Notifier
from .util import parse_url

LOG = logging.getLogger(__name__)
HEARTBEAT_TIME = 120
MESSAGE_RESPONSE_TIME = 5.0

class QueuedWrite(NamedTuple):
    """Entries in the write queue use this structure."""
    msg: str
    response_cmd: str | None
    timeout: float = 5.0
    raw: bool = False


class Connection:
    """Manage connection to ElkM1 panel."""

    def __init__(self, url: str, notifier: Notifier):
        self._url = url
        self._notifier = notifier

        self._writer: asyncio.StreamWriter | None = None
        self._awaiting_response_command: str | None = None
        self._paused = False
        self._heartbeat_event = asyncio.Event()
        self._message_timer_event = asyncio.Event()
        self._write_queue: deque[QueuedWrite] = deque()
        self._check_write_queue = asyncio.Event()
        self._response_received = asyncio.Event()
        self._tasks: set[Optional[asyncio.Task]] = set()
        self._response_timeout_task: Optional[asyncio.TimerHandle] = None

    async def connect(self) -> None:
        """Create connection to Elk."""

        LOG.info("Connecting to ElkM1 at %s", self._url)
        connection_retry_time = 1
        scheme, dest, param, ssl_context = parse_url(self._url)
        while True:
            if scheme == "serial":
                coro = serial_asyncio.open_serial_connection(port=dest, baudrate=param)
            else:
                coro = asyncio.open_connection(host=dest, port=param, ssl=ssl_context)
            try:
                reader, self._writer = await asyncio.wait_for(coro, timeout=30)
            except (ValueError, OSError, asyncio.TimeoutError) as err:
                # if self._connection_retry_time <= 0:
                #     return
                LOG.warning(
                    "Could not connect to ElkM1 (%s). Retrying in %d seconds",
                    err,
                    connection_retry_time,
                )
                await asyncio.sleep(connection_retry_time)
                connection_retry_time = min(60, connection_retry_time * 2)
                continue

            if scheme != "serial":
                self._tasks.add(asyncio.create_task(self._heartbeat_timer()))
            self._tasks.add(asyncio.create_task(self._read(reader)))
            self._tasks.add(asyncio.create_task(self._write()))

            self._notifier.notify("connected", {})
            break

    async def _read(self, reader: asyncio.StreamReader) -> None:
        read_buffer = ""
        while True:
            data = await reader.read(1000)
            if not data:
                break

            self._heartbeat()

            read_buffer += data.decode("ISO-8859-1")
            while "\r\n" in read_buffer:
                line, read_buffer = read_buffer.split("\r\n", 1)

                if get_elk_command(line) == self._awaiting_response_command:
                    self._response_received.set()
                    self._check_write_queue.set()

                LOG.debug("got_data '%s'", line)
                try:
                    decoded = decode(line)
                    if decoded:
                        self._notifier.notify(decoded[0], decoded[1])
                except (ValueError, AttributeError) as exc:
                    LOG.error("Invalid message '%s'", data, exc_info=exc)
        self._tasks.remove(asyncio.current_task())

    async def _write(self) -> None:
        while True:
            await self._check_write_queue.wait()
            self._check_write_queue.clear()
            if not self._writer:
                break

            if self._awaiting_response_command or not self._write_queue or self._paused:
                continue

            q_entry = self._write_queue.popleft()

            if not q_entry.raw:
                cksum = (256 - reduce(lambda x, y: x + y, map(ord, q_entry.msg))) % 256
                msg = f"{q_entry.msg}{cksum:02X}\r\n"
            else:
                msg = q_entry.msg + "\r\n"

            LOG.debug("write_data '%s'", msg[:-2])
            self._writer.write((msg).encode())

            if not q_entry.response_cmd:
                continue

            self._awaiting_response_command = q_entry.response_cmd
            try:
                async with async_timeout.timeout(MESSAGE_RESPONSE_TIME):
                    await self._response_received.wait()
            except asyncio.TimeoutError:
                self._notifier.notify("timeout", {"msg_code": q_entry.response_cmd})
                pass
            self._response_received.clear()
            self._awaiting_response_command = None

        self._tasks.remove(asyncio.current_task())

    def send(self, msg: MessageEncode, priority_send: bool = False) -> None:
        """Send a message to Elk."""
        q_entry = QueuedWrite(msg.message, msg.response_command)
        if priority_send:
            self._write_queue.appendleft(q_entry)
        else:
            self._write_queue.append(q_entry)
        self._check_write_queue.set()

    def send_raw(self, msg: str) -> None:
        """Send a raw message to Elk (no checksum will be added)."""
        self._write_queue.append(QueuedWrite(msg, None, raw=True))
        self._check_write_queue.set()

    def is_connected(self) -> bool:
        """Is the connection active?"""
        return self._writer is not None

    def pause(self) -> None:
        """Pause the connection from sending/receiving."""
        # self._cleanup() TODO
        self._write_queue.clear()
        self._paused = True

    def resume(self) -> None:
        """Restart the connection from sending/receiving."""
        self._paused = False

    def disconnect(self) -> None:
        """Disconnect and cleanup."""
        if self._writer:
            self._writer.close()
            self._writer = None
        self._write_queue.clear()
        self._check_write_queue.set()
        self._notifier.notify("disconnected", {})

    def _heartbeat(self) -> None:
        self._heartbeat_event.set()

    async def _heartbeat_timer(self) -> None:
        while True:
            self._heartbeat_event.clear()
            try:
                async with async_timeout.timeout(HEARTBEAT_TIME):
                    await self._heartbeat_event.wait()
            except asyncio.TimeoutError:
                if self._paused:
                    continue
                LOG.warning("ElkM1 connection heartbeat timed out, disconnecting")
                self.disconnect()
                await self.connect()
                break
        self._tasks.remove(asyncio.current_task())
