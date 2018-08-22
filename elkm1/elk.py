"""Master class that combines all ElkM1 pieces together."""

import asyncio
import logging
from importlib import import_module
import serial_asyncio

from .message import message_decode
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
        self.connection_lost_callbk = None
        self._connection_retry_timer = 1

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
        module = import_module('elkm1.'+element)
        class_ = getattr(module, element.capitalize())
        setattr(self, element, class_(self))

    async def _connect(self, connection_lost_callbk=None):
        """Asyncio connection to Elk."""
        self.connection_lost_callbk = connection_lost_callbk
        url = self._config['url']
        LOG.debug("Elk connect to %s", url)
        scheme, dest, param, ssl_context = parse_url(url)
        try:
            if scheme == 'serial':
                # pylint: disable=C0330
                _coro = await serial_asyncio.create_serial_connection(self.loop,
                            lambda: Connection(self.loop,
                            self._connected, self._disconnected, self._got_data),
                            dest, baudrate=param)
            else:
                # pylint: disable=C0330
                _coro = await self.loop.create_connection(
                        lambda: Connection(self.loop,
                        self._connected, self._disconnected, self._got_data),
                        host=dest, port=param, ssl=ssl_context)
        except:
            LOG.debug("Connection failed. Retrying in %d seconds",
                      self._connection_retry_timer)
            self.loop.call_later(self._connection_retry_timer, self.connect)
            self._connection_retry_timer = 2 * self._connection_retry_timer \
                if self._connection_retry_timer < 64 else 120

    def _connected(self, _transport, conn):
        """Login and sync the ElkM1 panel to memory."""
        self._conn = conn
        self._connection_retry_timer = 1
        if url_scheme_is_secure(self._config['url']):
            self._conn.write_data(self._config['userid'], raw=True)
            self._conn.write_data(self._config['password'], raw=True)
        #self.loop.call_later(30, call_sync_handlers)
        call_sync_handlers()

    def _disconnected(self):
        LOG.debug("elk disconnected callback")
        self._conn = None
        self.loop.call_later(self._connection_retry_timer, self.connect)

    def _got_data(self, data): # pylint: disable=no-self-use
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
        coro = self._connect()
        asyncio.ensure_future(coro)

    def run(self):
        """Enter the asyncio loop."""
        self.loop.run_forever()

    def send(self, msg):
        """Send a message to Elk panel."""
        self._conn.write_data(msg.message, msg.response_command)

    def pause(self):
        """Pause the connection from sending/receiving."""
        self._conn.pause()

    def resume(self):
        """Restart the connection from sending/receiving."""
        self._conn.resume()
