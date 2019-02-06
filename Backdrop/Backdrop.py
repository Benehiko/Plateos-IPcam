import asyncio
from multiprocessing import Process
import janus

import server
from Backdrop.BackdropHandler import BackdropHandler


# noinspection PyBroadException
class Backdrop:

    def __init__(self):
        self.main_loop = asyncio.get_event_loop()
        self.obj_queue = janus.Queue(loop=self.main_loop)
        self.cv_queue = janus.Queue(loop=self.main_loop)
        self.frames_queue = janus.Queue(loop=self.main_loop)
        self.backdrophandler = BackdropHandler()

    def start(self):
        while True:
            p = Process(target=self.backdrophandler.start,
                        args=(self.main_loop, self.obj_queue, self.cv_queue, self.frames_queue))
            p.start()
            p2 = Process(target=server.start, args=(self.obj_queue.sync_q, self.cv_queue.sync_q))
            p2.start()
            try:
                p.join()
                p2.join()
            except KeyboardInterrupt:
                break
