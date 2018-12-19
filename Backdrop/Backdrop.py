from multiprocessing import Process

from Backdrop.BackdropHandler import BackdropHandler


# noinspection PyBroadException
class Backdrop:

    def __init__(self):
        self.backdrophandler = BackdropHandler(self)

    def scan(self):
        while True:
            try:
                p = Process(target=self.backdrophandler.start())
                p.start()
                p.join()
            except Exception as e:
                print(e)
                pass
