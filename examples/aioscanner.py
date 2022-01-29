import asyncio
import logging
import pprint

from elkm1_lib.discovery import AIOELKDiscovery

logging.basicConfig(level=logging.DEBUG)


async def go():
    scanner = AIOELKDiscovery()
    pprint.pprint(await scanner.async_scan())


asyncio.run(go())
