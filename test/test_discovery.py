import asyncio
import contextlib
from unittest.mock import MagicMock, patch

import pytest

from elkm1_lib.discovery import (
    AIOELKDiscovery,
    ELKDiscovery,
    ElkSystem,
)


@pytest.fixture
async def mock_discovery_aio_protocol():
    """Fixture to mock an asyncio connection."""
    loop = asyncio.get_running_loop()
    future = asyncio.Future()

    async def _wait_for_connection():
        transport, protocol = await future
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        return transport, protocol

    async def _mock_create_datagram_endpoint(func, sock=None):
        protocol: ELKDiscovery = func()
        transport = MagicMock()
        protocol.connection_made(transport)
        with contextlib.suppress(asyncio.InvalidStateError):
            future.set_result((transport, protocol))
        return transport, protocol

    with patch.object(loop, "create_datagram_endpoint", _mock_create_datagram_endpoint):
        yield _wait_for_connection


@pytest.mark.asyncio
async def test_async_scanner_specific_address(mock_discovery_aio_protocol):
    """Test scanner with a specific address."""
    scanner = AIOELKDiscovery()

    task = asyncio.ensure_future(
        scanner.async_scan(timeout=10, address="192.168.209.56")
    )
    _, protocol = await mock_discovery_aio_protocol()
    protocol.datagram_received(
        b"M1XEP\x00@\x9d\xb1\xad\x03\xc0\xa8\xd18\n)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01",
        ("192.168.209.56", 2362),
    )
    await task
    assert scanner.found_devices == [
        ElkSystem(
            mac_address="00:40:9D:B1:AD:03", ip_address="192.168.209.56", port=2601
        )
    ]


@pytest.mark.asyncio
async def test_async_scanner_broadcast(mock_discovery_aio_protocol):
    """Test scanner with a broadcast."""
    scanner = AIOELKDiscovery()

    task = asyncio.ensure_future(scanner.async_scan(timeout=0.01))
    _, protocol = await mock_discovery_aio_protocol()
    protocol.datagram_received(
        b"M1XEP\x00@\x9d\xb1\xad\x03\xc0\xa8\xd18\n)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01",
        ("192.168.209.56", 2362),
    )
    await task
    assert scanner.found_devices == [
        ElkSystem(
            mac_address="00:40:9D:B1:AD:03", ip_address="192.168.209.56", port=2601
        )
    ]
