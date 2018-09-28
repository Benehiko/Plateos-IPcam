from threading import Thread

from Backdrop.BackdropHandler import BackdropHandler
from Network.PortScanner import PortScanner
from tess.tesseract import Tess


# noinspection PyBroadException
class Backdrop:

    def __init__(self, args, iprange, url):
        self.backdrophandler = BackdropHandler(self, scanner=PortScanner(), iprange=iprange, args=args, url=url)

    async def scan(self):
        while True:
            t = Thread(target=self.backdrophandler.start()).start()
            t.join()
