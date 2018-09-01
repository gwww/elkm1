"""Master class that combines all ElkM1 pieces together."""

import asyncio
from functools import partial
import logging
from importlib import import_module
import serial_asyncio

from .message import add_message_handler, message_decode
from .proto import Connection
from .util import call_sync_handlers, parse_url, url_scheme_is_secure

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

        self._heartbeat = None
        add_message_handler('XK', self._xk_handler)

        # Setup for all the types of elements tracked
        if 'element_list' in config:
            self.element_list = config['element_list']
        else:
            self.element_list = ['panel', 'zones', 'lights', 'areas',
                                 'tasks', 'keypads', 'outputs', 'thermostats',
                                 'counters', 'settings', 'users']
        for element in self.element_list:
            self._create_element(element)

    def _create_element(self, element):
        module = import_module('elkm1_lib.'+element)
        class_ = getattr(module, element.capitalize())
        setattr(self, element, class_(self))

    async def _connect(self, connection_lost_callbk=None):
        """Asyncio connection to Elk."""
        self.connection_lost_callbk = connection_lost_callbk
        url = self._config['url']
        LOG.info("Connecting to ElkM1 at %s", url)
        scheme, dest, param, ssl_context = parse_url(url)
        conn = partial(Connection, self.loop, self._connected,
                       self._disconnected, self._got_data)
        try:
            if scheme == 'serial':
                await serial_asyncio.create_serial_connection(
                    self.loop, conn, dest, baudrate=param)
            else:
                await asyncio.wait_for(self.loop.create_connection(
                    conn, host=dest, port=param, ssl=ssl_context), timeout=30)
        except (ValueError, OSError, asyncio.TimeoutError) as err:
            LOG.warning("Could not connect to ElkM1 (%s). Retrying in %d seconds",
                        err, self._connection_retry_timer)
            self.loop.call_later(self._connection_retry_timer, self.connect)
            self._connection_retry_timer = 2 * self._connection_retry_timer \
                if self._connection_retry_timer < 32 else 60

    def _connected(self, transport, conn):
        """Login and sync the ElkM1 panel to memory."""
        LOG.info("Connected to ElkM1")
        self._conn = conn
        self._transport = transport
        self._connection_retry_timer = 1
        if url_scheme_is_secure(self._config['url']):
            self._conn.write_data(self._config['userid'], raw=True)
            self._conn.write_data(self._config['password'], raw=True)
        call_sync_handlers()
        if not self._config['url'].startswith('serial://'):
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
        LOG.warning("ElkM1 disconnected")
        self._conn = None
        self.loop.call_later(self._connection_retry_timer, self.connect)
        if self._heartbeat:
            self._heartbeat.cancel()
            self._heartbeat = None

    def _got_data(self, data):  # pylint: disable=no-self-use
        LOG.debug("got_data '%s'", data)
        try:
            message_decode(data)
        except ValueError as err:
            LOG.debug(err)

    def is_connected(self):
        """Status of connection to Elk."""
        return self._conn is not None

    def connect(self):
        """Connect to the panel"""
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
