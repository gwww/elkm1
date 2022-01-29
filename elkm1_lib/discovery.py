import asyncio
import logging
import socket
import time
from dataclasses import dataclass
from struct import unpack
from typing import Callable, Dict, List, Optional, Tuple

_LOGGER = logging.getLogger(__name__)


@dataclass
class ElkSystem:
    """An ELKM1 system."""

    mac_address: str
    ip_address: str
    port: int


def create_udp_socket(discovery_port: int) -> socket.socket:
    """Create a udp socket used for communicating with the device."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(("", 0))
    sock.setblocking(False)
    return sock


class ELKDiscovery(asyncio.DatagramProtocol):
    def __init__(
        self,
        destination: Tuple[str, int],
        on_response: Callable[[bytes, Tuple[str, int]], None],
    ) -> None:
        self.transport = None
        self.destination = destination
        self.on_response = on_response

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Trigger on_response."""
        self.on_response(data, addr)

    def error_received(self, ex: Optional[Exception]) -> None:
        """Handle error."""
        _LOGGER.error("ELKDiscovery error: %s", ex)

    def connection_lost(self, ex: Optional[Exception]) -> None:
        """Do nothing on connection lost."""


def _decode_data(raw_response):
    """Decode an ELK discovery response packet."""
    remain = raw_response[5:]
    data = remain[:14]
    (
        mac1,
        mac2,
        mac3,
        mac4,
        mac5,
        mac6,
        ipv4_1,
        ipv4_2,
        ipv4_3,
        ipv4_4,
        port,
        _,
    ) = unpack("!6B4BHH", data)
    mac_address = ":".join(
        [
            format(val, "02x").upper().zfill(2)
            for val in (mac1, mac2, mac3, mac4, mac5, mac6)
        ]
    )
    ip_address = f"{ipv4_1}.{ipv4_2}.{ipv4_3}.{ipv4_4}"

    return ElkSystem(mac_address, ip_address, port)


class AIOELKDiscovery:
    """A 30303 discovery scanner."""

    DISCOVERY_PORT = 2362
    BROADCAST_FREQUENCY = 3
    DISCOVER_MESSAGE = b"XEPID"
    BROADCAST_ADDRESS = "<broadcast>"

    def __init__(self) -> None:
        self.found_devices: List[ElkSystem] = []

    def _destination_from_address(self, address: Optional[str]) -> Tuple[str, int]:
        if address is None:
            address = self.BROADCAST_ADDRESS
        return (address, self.DISCOVERY_PORT)

    def _process_response(
        self,
        data: Optional[bytes],
        from_address: Tuple[str, int],
        address: Optional[str],
        response_list: Dict[str, ELKDiscovery],
    ) -> bool:
        """Process a response.

        Returns True if processing should stop
        """
        if (
            data is None
            or data == self.DISCOVER_MESSAGE
            or not data.startswith(b"M1XEP")
        ):
            return
        try:
            response_list[from_address] = _decode_data(data)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning("Failed to decode response from %s: %s", from_address, ex)
            return False
        return from_address[0] == address

    async def _async_run_scan(
        self,
        transport: asyncio.DatagramTransport,
        destination: Tuple[str, int],
        timeout: int,
        found_all_future: "asyncio.Future[bool]",
    ) -> None:
        """Send the scans."""
        _LOGGER.debug("discover: %s => %s", destination, self.DISCOVER_MESSAGE)
        transport.sendto(self.DISCOVER_MESSAGE, destination)
        quit_time = time.monotonic() + timeout
        remain_time = timeout
        while True:
            time_out = min(remain_time, timeout / self.BROADCAST_FREQUENCY)
            if time_out <= 0:
                return
            try:
                await asyncio.wait_for(
                    asyncio.shield(found_all_future), timeout=time_out
                )
            except asyncio.TimeoutError:
                if time.monotonic() >= quit_time:
                    return
                # No response, send broadcast again in cast it got lost
                _LOGGER.debug("discover: %s => %s", destination, self.DISCOVER_MESSAGE)
                transport.sendto(self.DISCOVER_MESSAGE, destination)
            else:
                return  # found_all
            remain_time = quit_time - time.monotonic()

    async def async_scan(
        self, timeout: int = 10, address: Optional[str] = None
    ) -> List[ELKDiscovery]:
        """Discover ELK devices."""
        sock = create_udp_socket(self.DISCOVERY_PORT)
        destination = self._destination_from_address(address)
        found_all_future = asyncio.Future()
        response_list = {}

        def _on_response(data: bytes, addr: Tuple[str, int]) -> None:
            _LOGGER.debug("discover: %s <= %s", addr, data)
            if self._process_response(data, addr, address, response_list):
                found_all_future.set_result(True)

        transport, _ = await asyncio.get_running_loop().create_datagram_endpoint(
            lambda: ELKDiscovery(
                destination=destination,
                on_response=_on_response,
            ),
            sock=sock,
        )
        try:
            await self._async_run_scan(
                transport, destination, timeout, found_all_future
            )
        finally:
            transport.close()

        self.found_devices = list(response_list.values())
        return self.found_devices
