"""Master class that combines all ElkM1 pieces together."""

import asyncio
import logging
from importlib import import_module

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

        # Setup for all the types of elements tracked
        if 'element_list' in config:
            self.element_list = config['element_list']
        else:
            self.element_list = ['panel', 'zones', 'lights', 'areas',
                                 'tasks', 'keypads', 'outputs', 'thermostats',
                                 'counters', 'settings']
        for element in self.element_list:
            self._create_element(element)

    def _create_element(self, element):
        module = import_module('elkm1.'+element)
        class_ = getattr(module, element.capitalize())
        setattr(self, element, class_(self))

    async def connect(self, connection_lost_callbk=None):
        """Asyncio connection to Elk."""
        self.connection_lost_callbk = connection_lost_callbk
        url = self._config['url']
        LOG.debug("Elk connect to %s", url)
        _scheme, host, port, ssl_context = parse_url(url)
        # pylint: disable=C0330
        _coro = await self.loop.create_connection(
            lambda: Connection(loop=self.loop,
                connection_made=self._connection_made,
                connection_lost=self._connection_lost,
                gotdata_callbk=self._got_data),
                host=host, port=port, ssl=ssl_context)

    def run(self):
        """Enter the asyncio loop."""
        self.loop.run_forever()

    def _got_data(self, data): # pylint: disable=no-self-use
        LOG.debug("got_data '%s'", data)
        try:
            message_decode(data)
        except ValueError as err:
            LOG.debug(err)

    def send(self, msg):
        """Send a message to Elk panel."""
        self._conn.write_data(msg.message, msg.response_command)

    def _connection_made(self, _transport, conn):
        """Login and sync the ElkM1 panel to memory."""
        self._conn = conn
        if url_scheme_is_secure(self._config['url']):
            self._conn.write_data(self._config['userid'], raw=True)
            self._conn.write_data(self._config['password'], raw=True)
        call_sync_handlers()

    def _connection_lost(self):
        # TODO: callbk out of library
        self._conn = None
