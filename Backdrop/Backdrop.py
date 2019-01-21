from multiprocessing import Process, Queue

import server
from Backdrop.BackdropHandler import BackdropHandler


# noinspection PyBroadException
class Backdrop:

    def __init__(self):
        self.obj_queue = Queue()
        self.cv_queue = Queue()
        self.backdrophandler = BackdropHandler()

    def start(self):
        while True:
            p = Process(target=self.backdrophandler.start, args=(self.obj_queue, self.cv_queue))
            p.start()
            p2 = Process(target=server.start, args=(self.obj_queue, self.cv_queue))
            p2.start()
            try:
                p.join()
                p2.join()
            except KeyboardInterrupt:
                break
