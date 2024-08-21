#!/usr/bin/env python

import logging
import os

from elkm1_lib import Elk
from elkm1_lib.message import ua_encode

LOG = logging.getLogger(__name__)


class MyApp:
    def __init__(self, url, user_code):
        # Setting element list to empty list means no elements are synced on startup
        # i.e.: saves startup sync time if you don't need it!
        self.elk = Elk({"url": url, "element_list": []})

        # Add some handlers here which get called when their respective event occurs.
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.connect()

        self.user_code = user_code

        # Start the asyncio event loop.
        self.elk.run()

    def disconnected(self):
        """The ElkM1 panel has disconnect."""
        print("Disconnected!!!")
        exit(0)  # Just exit since this is a demo, might want to try and reconnect.

    def connected(self):
        """The ElkM1 is connected - we can communicate with the panel now!"""
        print("Connected!!!")

    def sync_complete(self):
        """
        On startup of the lib, we synchronize the status of all the elements on
        the panel to the lib. Things such as zone status, temperature, etc. This
        handler is called when the sychronization is complete. It's a good spot
        for your app to sending its own messages to the ElkM1.
        """
        print("Sync complete!!!")

        # Add a method that is called when a response to a UA message is received.
        self.elk.add_handler("UA", self.ua_response)

        # Send a UA message
        self.elk.send(ua_encode(self.user_code))

    def ua_response(self, **kwargs):
        """Got a response to our UA message!"""
        print(kwargs)

        # Got the UA response! Add your own app code here.
        # We just disconnect since we got the one response we want.
        self.elk.disconnect()


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    # Uses an environment variable for simplicity; could be command line argument
    url = os.environ.get("ELKM1_URL")
    if not url:
        print("Specify url to connect to in ELKM1_URL environment variable")
        exit(0)
    _ = MyApp(url, 8813)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
