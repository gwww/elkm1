"""Master class that combines all ElkM1 pieces together."""

import asyncio
from functools import partial
import logging
from importlib import import_module
import serial_asyncio

from .message import MessageDecode, sd_encode, ua_encode
from .proto import Connection
from .util import parse_url, url_scheme_is_secure

LOG = logging.getLogger(__name__)


class Elk:
    """Represents all the components on an Elk panel."""

    def __init__(self, config, loop=None):
        """Initialize a new Elk instance."""
        self.loop = loop if loop else asyncio.get_event_loop()
        self._config = config
        self._conn = None
        self._transport = None
        self.connection_lost_callbk = None
        self._connection_retry_timer = 1
        self._message_decode = MessageDecode()
        self._sync_handlers = []
        self._descriptions_in_progress = {}
        self._sync_event = asyncio.Event()
        self._heartbeat = None
        self._invalid_auth = False
        self._connection_retry_task = None
        self._disconnect_requested = False

        self.add_handler("XK", self._xk_handler)
        self.add_handler("SD", self._sd_handler)

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
        # We send a "ua" command at the end of the
        # sync to indicate the sync is done.
        self.add_handler("UA", self._sync_complete)

        for element in self.element_list:
            self._create_element(element)

    def _sync_complete(self, **kwargs):
        self._sync_event.set()

    def _create_element(self, element):
        module = import_module("elkm1_lib." + element)
        class_ = getattr(module, element.capitalize())
        setattr(self, element, class_(self))

    async def _connect(self, connection_lost_callbk=None):
        """Asyncio connection to Elk."""
        self.connection_lost_callbk = connection_lost_callbk
        self._invalid_auth = False
        url = self._config["url"]
        LOG.info("Connecting to ElkM1 at %s", url)
        scheme, dest, param, ssl_context = parse_url(url)
        conn = partial(
            Connection,
            self.loop,
            self._connected,
            self._disconnected,
            self._got_data,
            self._timeout,
        )
        try:
            if scheme == "serial":
                await serial_asyncio.create_serial_connection(
                    self.loop, conn, dest, baudrate=param
                )
            else:
                await asyncio.wait_for(
                    self.loop.create_connection(
                        conn, host=dest, port=param, ssl=ssl_context
                    ),
                    timeout=30,
                )
        except (ValueError, OSError, asyncio.TimeoutError) as err:
            if self._disconnect_requested:
                # disconnect called while trying to reconnect
                return
            LOG.warning(
                "Could not connect to ElkM1 (%s). Retrying in %d seconds",
                err,
                self._connection_retry_timer,
            )
            self._connection_retry_task = self.loop.call_later(
                self._connection_retry_timer, self.connect
            )
            self._connection_retry_timer = (
                2 * self._connection_retry_timer
                if self._connection_retry_timer < 32
                else 60
            )

    def _connected(self, transport, conn):
        """Login and sync the ElkM1 panel to memory."""
        LOG.info("Connected to ElkM1")
        self._conn = conn
        self._transport = transport
        self._connection_retry_timer = 1
        if url_scheme_is_secure(self._config["url"]):
            self._conn.write_data(self._config["userid"], raw=True)
            self._conn.write_data(self._config["password"], raw=True)
        self.call_sync_handlers()
        if not self._config["url"].startswith("serial://"):
            self._heartbeat = self.loop.call_later(120, self._reset_connection)

    def _reset_connection(self):
        LOG.warning("ElkM1 connection heartbeat timed out, disconnecting")
        self._transport.close()
        self._heartbeat = None

    # pylint: disable=unused-argument
    def _xk_handler(self, real_time_clock):
        if not self._heartbeat:
            return
        self._heartbeat.cancel()
        self._heartbeat = self.loop.call_later(120, self._reset_connection)

    def _disconnected(self):
        LOG.warning("ElkM1 at %s disconnected", self._config["url"])
        self._conn = None
        self._connection_retry_task = self.loop.call_later(
            self._connection_retry_timer, self.connect
        )
        if self._heartbeat:
            self._heartbeat.cancel()
            self._heartbeat = None

    def add_handler(self, msg_type, handler):
        self._message_decode.add_handler(msg_type, handler)

    def _got_data(self, data):  # pylint: disable=no-self-use
        LOG.debug("got_data '%s'", data)
        try:
            self._message_decode.decode(data)
        except (ValueError, AttributeError) as err:
            if (
                not len(data)
                or data.startswith("Username: ")
                or data.startswith("Password: ")
            ):
                return
            elif data.startswith("Username/Password not found"):
                LOG.error("Invalid username or password.")
                self.disconnect()
                self._invalid_auth = True
                self._sync_event.set()
            elif "Login successful" in data:
                LOG.info("Successful login.")
                return

            LOG.debug(err)

    def _timeout(self, msg_code):
        self._message_decode.timeout_handler(msg_code)

    def add_sync_handler(self, sync_handler):
        """Register a fn that synchronizes part of the panel."""
        self._sync_handlers.append(sync_handler)

    def call_sync_handlers(self):
        """Invoke the synchronization handlers."""
        LOG.debug("Synchronizing panel...")
        self._sync_event.clear()
        for sync_handler in self._sync_handlers:
            sync_handler()
        # We send an empty "ua" message at the end of the sync
        # so we can watch for the "UA" response to come back
        # and know that the sync has completed.
        self.send(ua_encode(0))

    async def sync_complete(self):
        return await self._sync_event.wait()

    # pylint: disable=unused-argument
    def _sd_handler(self, desc_type, unit, desc, show_on_keypad):
        """Text description"""
        if desc_type not in self._descriptions_in_progress:
            LOG.debug("Text description response ignored for " + str(desc_type))
            return

        (max_units, results, callback) = self._descriptions_in_progress[desc_type]
        if unit < 0 or unit >= max_units:
            callback(results)
            del self._descriptions_in_progress[desc_type]
            return

        results[unit] = desc
        self.send(sd_encode(desc_type=desc_type, unit=unit + 1))

    def is_connected(self):
        """Status of connection to Elk."""
        return self._conn is not None

    def connect(self):
        """Connect to the panel"""
        self._disconnect_requested = False
        asyncio.ensure_future(self._connect())

    def run(self):
        """Enter the asyncio loop."""
        self.loop.run_forever()

    def send(self, msg):
        """Send a message to Elk panel."""
        if self._conn:
            self._conn.write_data(msg.message, msg.response_command)

    def pause(self):
        """Pause the connection from sending/receiving."""
        if self._conn:
            self._conn.pause()

    def resume(self):
        """Restart the connection from sending/receiving."""
        if self._conn:
            self._conn.resume()

    def disconnect(self):
        """Disconnect the connection from sending/receiving."""
        self._disconnect_requested = True
        if self._conn:
            self._conn.stop()
            self._conn = None
        if self._connection_retry_task:
            self._connection_retry_task.cancel()
            self._connection_retry_task = None
        if self._transport:
            self._transport.close()
            self._transport = None
        if self._heartbeat:
            self._heartbeat.cancel()
            self._heartbeat = None

    @property
    def invalid_auth(self):
        """Last session was disconnected due to invalid auth details."""
        return self._invalid_auth
