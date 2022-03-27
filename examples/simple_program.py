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
        self.elk.add_handler("disconnected", self.disconnected)
        self.elk.add_handler("connected", self.connected)
        self.elk.add_handler("sync_complete", self.sync_complete)
        self.elk.connect()

        self.user_code = user_code

        self.elk.run()

    def disconnected(self):
        print("Disconnected!!!")
        self.elk = None
        exit(0)

    def connected(self):
        print("Connected!!!")

    def sync_complete(self):
        print("Sync complete!!!")
        self.elk.add_handler("UA", self.ua_response)
        self.elk.send(ua_encode(self.user_code))

    def ua_response(self, **kwargs):
        print(kwargs)
        self.elk.disconnect()


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(message)s")

    # Uses an environment variable for simplicity; could be command line argument
    url = os.environ.get("ELKM1_URL")
    if not url:
        print("Specify url to connect to in ELKM1_URL environment variable")
        exit(0)
    myapp = MyApp(url, 1234)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
