from multiprocessing import Process, Queue

import server
from Backdrop.BackdropHandler import BackdropHandler


# noinspection PyBroadException
class Backdrop:

    def __init__(self):
        self.obj_queue = Queue()
        self.backdrophandler = BackdropHandler()
        self.interface = server.Interface()

    def start(self):
        while True:
            p = Process(target=self.backdrophandler.start, args=(self.obj_queue,))
            p2 = Process(target=self.interface.start, args=(self.obj_queue,))
            p.start()
            p2.start()
            try:
                p2.join()
                p.join()
            except KeyboardInterrupt:
                break
