from multiprocessing import Process

from Backdrop.BackdropHandler import BackdropHandler
from Network.PortScanner import PortScanner


# noinspection PyBroadException
class Backdrop:

    def __init__(self, args, iprange, url):
        self.backdrophandler = BackdropHandler(self, scanner=PortScanner(), iprange=iprange, args=args, url=url)

    def scan(self):
        while True:
            try:
                p = Process(target=self.backdrophandler.start())
                p.start()
                p.join()
            except Exception as e:
                print(e)
                pass
