from functools import reduce

from elkm1_lib.message import decode
from elkm1_lib.notify import Notifier


def rx_msg(msg_code: str, msg: str, notifier: Notifier, zeros="00"):
    """
    Create a Elk received message, pass it to decode, and
    invoke the notifiers which will update the base element.
    """
    data = f"{len(msg)+len(zeros)+4:02X}{msg_code}{msg}{zeros}"
    cksum = 256 - reduce(lambda x, y: x + y, map(ord, data)) % 256
    decoded = decode(f"{data}{cksum:02X}")
    if decoded:
        notifier.notify(decoded[0], decoded[1])
