"""Master class that combines all ElkM1 pieces together."""

import asyncio
import logging
from functools import partial
from importlib import import_module

import serial_asyncio

from .message import MessageDecode, sd_encode, ua_encode
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
        self._sync_event = asyncio.Event()
        self._invalid_auth = False
        self._reconnect_task = None

        self.connected_callback = None
        self.disconnected_callback = None

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

        for element in self.element_list:
            module = import_module("elkm1_lib." + element)
            class_ = getattr(module, element.capitalize())
            setattr(self, element, class_(self))

    def _sync_complete(self, **kwargs):  # pylint: disable=unused-argument
        self._sync_event.set()

    async def _connect(self):
        """Asyncio connection to Elk."""
        self._invalid_auth = False
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
        if self._connection_retry_time > 0:
            self._reconnect_task = self.loop.call_later(
                self._connection_retry_time, self._reconnect
            )
            if self._connection_retry_time < 32:
                self._connection_retry_time *= 2
            else:
                self._connection_retry_time = 60

    def _connected(self, connection):
        """Login and sync the ElkM1 panel to memory."""
        LOG.info("Connected to ElkM1")
        self._connection = connection
        self._connection_retry_time = 1
        if url_scheme_is_secure(self._config["url"]):
            self._connection.write_data(self._config["userid"], raw=True)
            self._connection.write_data(self._config["password"], raw=True)
        self.call_sync_handlers()
        if self.connected_callback:
            self.connected_callback(self)

    def _reconnect(self):
        asyncio.ensure_future(self._connect())

    def _disconnected(self):
        LOG.warning("ElkM1 at %s disconnected", self._config["url"])
        self._connection = None
        self._start_connection_retry_timer()
        if self.disconnected_callback:
            self.disconnected_callback(self)

    def add_handler(self, msg_type, handler):
        """Add handler for incoming message."""
        self._message_decode.add_handler(msg_type, handler)

    def _got_data(self, data):  # pylint: disable=no-self-use
        LOG.debug("got_data '%s'", data)
        try:
            self._message_decode.decode(data)
        except (ValueError, AttributeError) as exc:
            if not data:
                return
            if data.startswith("Username: ") or data.startswith("Password: ")
                return

            if data.startswith("Username/Password not found"):
                LOG.error("Invalid username or password.")
                self.disconnect()
                self._invalid_auth = True
                self._sync_event.set()
            elif "Login successful" in data:
                LOG.info("Successful login.")
            else:
                LOG.exception("Invalid message '%s'", data, exc)

    def _timeout(self, msg_code):
        self._message_decode.timeout_handler(msg_code)

    def call_sync_handlers(self):
        """Invoke the synchronization handlers."""
        LOG.debug("Synchronizing panel...")
        self._sync_event.clear()

        for element in self.element_list:
            getattr(self, element).sync()
        self.send(ua_encode(0))  # Used to mark end of sync

    async def sync_complete(self):
        """Called when sync is complete with the panel."""
        return await self._sync_event.wait()

    def is_connected(self):
        """Status of connection to Elk."""
        return self._connection is not None

    def connect(self, connected_callback=None, disconnected_callback=None):
        """Connect to the panel"""
        self.connected_callback = connected_callback
        self.disconnected_callback = disconnected_callback
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
        self._connection_retry_time = -1
        if self._connection:
            self._connection.close()
            self._connection = None
        if self._reconnect_task:
            self._reconnect_task.cancel()
            self._reconnect_task = None

    @property
    def invalid_auth(self):
        """Last session was disconnected due to invalid auth details."""
        return self._invalid_auth
