"""Read a data file off the card and store on FS."""
import time

import sys

from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.CardConnectionObserver import ConsoleCardConnectionObserver
from smartcard.System import readers
import logging
import functools
from desfire.protocol import DESFire
from desfire.pcsc import PCSCDevice
from rainbow_logging_handler import RainbowLoggingHandler

IGNORE_EXCEPTIONS = (
    KeyboardInterrupt,
    MemoryError,
)


def setup_logging():
    # Setup Python root logger to DEBUG level
    logger = logging.getLogger()
    logger.setLevel(logging.CRITICAL)
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s %(funcName)s():%(lineno)d\t%(message)s"
    )  # same as default

    # Add colored log handlign to sys.stderr
    handler = RainbowLoggingHandler(sys.stderr)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def catch_gracefully():
    """Function decorator to show any Python exceptions occured inside a function.

    Use when the underlying thread main loop does not provide satisfying exception output.
    """

    def _outer(func):
        @functools.wraps(func)
        def _inner(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, IGNORE_EXCEPTIONS):
                    raise
                else:
                    logger.error("Catched exception %s when running %s", e, func)
                    logger.exception(e)

        return _inner

    return _outer


DUMP_NAME = "carddump.bin.tmp"

logger = None


class MyObserver(CardObserver):
    """Observe when a card is inserted. Then try to run DESFire application listing against it."""

    @catch_gracefully()
    def update(self, observable, actions):
        (addedcards, removedcards) = actions

   

        for card in addedcards:
     

            if not card.atr:
                logger.warn("Did not correctly detected card insert")
                continue

            connection = card.createConnection()
            connection.connect()
            card.connection = connection.component

            # This will log raw card traffic to console
            connection.addObserver(ConsoleCardConnectionObserver())

            # connection object itself is CardConnectionDecorator wrapper
            # and we need to address the underlying connection object
            # directly
         

            desfire = DESFire(PCSCDevice(connection.component))
            applications = desfire.get_applications()

            if 0x007080f4 in applications:
                app = 0x007080f4
                desfire.select_application(app)
          
                data = desfire.read_data_file(0)
                logger.critical("Data: %d", int.from_bytes(data[5:13]))


       


def main():
    global logger
    global consumer
    global event_monitor

    setup_logging()
    logger = logging.getLogger(__name__)

    available_reader = readers()
    if not available_reader:
        sys.exit("No card readers detected")

    card_monitor = CardMonitor()
    card_observer = MyObserver()
    card_monitor.addObserver(card_observer)

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
