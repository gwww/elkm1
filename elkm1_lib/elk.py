"""Master class that combines all ElkM1 pieces together."""

import asyncio
import logging
from functools import partial
from importlib import import_module

import serial_asyncio

from .message import MessageDecode, ua_encode
from .proto import Connection
from .util import parse_url, url_scheme_is_secure

LOG = logging.getLogger(__name__)


class Elk:  # pylint: disable=too-many-instance-attributes
    """Represents all the components on an Elk panel."""

    def __init__(self, config, loop=None):
        """Initialize a new Elk instance."""
        self.loop = loop if loop else asyncio.get_event_loop()
        self._config = config
        self._connection = None
        self._connection_retry_time = 1
        self._message_decode = MessageDecode()
        self._reconnect_task = None

        # Setup for all the types of elements tracked
        if "element_list" in config:
            self.element_list = config["element_list"]
        else:
            self.element_list = [
                "panel",
                "zones",
                "lights",
                "areas",
                "tasks",
                "keypads",
                "outputs",
                "thermostats",
                "counters",
                "settings",
                "users",
            ]

        self.add_handler("UA", self._sync_complete)
        self.add_handler("login", self._login_status)

        for element in self.element_list:
            module = import_module("elkm1_lib." + element)
            class_ = getattr(module, element.capitalize())
            setattr(self, element, class_(self))

    def _sync_complete(self, **kwargs):  # pylint: disable=unused-argument
        self._message_decode.call_handlers("sync_complete", {})

        # So that other apps can send UA and not trigger sync_complete
        self.remove_handler("UA", self._sync_complete)

    def _login_status(self, succeeded):
        if not succeeded:
            self.disconnect()
            LOG.error("Invalid username or password.")

    async def _connect(self):
        """Asyncio connection to Elk."""
        url = self._config["url"]
        LOG.info("Connecting to ElkM1 at %s", url)
        scheme, dest, param, ssl_context = parse_url(url)
        heartbeat_time = 120 if not scheme == "serial" else -1

        connection = partial(
            Connection,
            self.loop,
            heartbeat_time,
            self._connected,
            self._disconnected,
            self._got_data,
            self._timeout,
        )
        try:
            if scheme == "serial":
                await serial_asyncio.create_serial_connection(
                    self.loop, connection, dest, baudrate=param
                )
            else:
                await asyncio.wait_for(
                    self.loop.create_connection(
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

    def _start_connection_retry_timer(self):
        timeout = self._connection_retry_time
        if timeout > 0:
            self._reconnect_task = self.loop.call_later(timeout, self._reconnect)
            self._connection_retry_time = min(60, timeout * 2)

    def _connected(self, connection):
        """Login and sync the ElkM1 panel to memory."""
        LOG.info("Connected to ElkM1")
        self._connection = connection
        self._connection_retry_time = 1
        if url_scheme_is_secure(self._config["url"]):
            self._connection.write_data(self._config["userid"], raw=True)
            self._connection.write_data(self._config["password"], raw=True)
        self._message_decode.call_handlers("connected", {})
        self.call_sync_handlers()

    def _reconnect(self):
        asyncio.ensure_future(self._connect())

    def _disconnected(self):
        LOG.warning("ElkM1 at %s disconnected", self._config["url"])
        self._connection = None
        self._start_connection_retry_timer()
        self._message_decode.call_handlers("disconnected", {})

    def add_handler(self, msg_type, handler):
        """Add handler."""
        self._message_decode.add_handler(msg_type, handler)

    def remove_handler(self, msg_type, handler):
        """Remove handler."""
        self._message_decode.remove_handler(msg_type, handler)

    def _got_data(self, data):
        LOG.debug("got_data '%s'", data)
        try:
            self._message_decode.decode(data)
        except (ValueError, AttributeError) as exc:
            LOG.error("Invalid message '%s'", data, exc_info=exc)

    def _timeout(self, msg_code):
        self._message_decode.call_handlers("timeout", {"msg_code": msg_code})

    def call_sync_handlers(self):
        """Invoke the synchronization handlers."""
        LOG.debug("Synchronizing panel...")

        for element in self.element_list:
            getattr(self, element).sync()
        self.send(ua_encode(0))  # Used to mark end of sync

    def is_connected(self):
        """Status of connection to Elk."""
        return self._connection is not None

    def connect(self):
        """Connect to the panel"""
        asyncio.ensure_future(self._connect())

    def run(self):
        """Enter the asyncio loop."""
        self.loop.run_forever()

    def send(self, msg):
        """Send a message to Elk panel."""
        if self._connection:
            self._connection.write_data(msg.message, msg.response_command)

    def pause(self):
        """Pause the connection from sending/receiving."""
        if self._connection:
            self._connection.pause()

    def resume(self):
        """Restart the connection from sending/receiving."""
        if self._connection:
            self._connection.resume()

    def disconnect(self):
        """Disconnect the connection from sending/receiving."""
        self._connection_retry_time = -1  # Stop future timeout reconnects
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None
