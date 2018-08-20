import datetime
import asyncio

from time import sleep
from multiprocessing import Process

from Network.PortScanner import PortScanner
from camera.Camera import Camera
from cvShapeHandler.imageprocessing import ImagePreProcessing
from tess.tesseract import Tess


class Backdrop:

    def __init__(self, args, iprange):
        self.iprange = iprange
        self.camera = []
        self.tess = Tess(backdrop=self)
        self.active = set()
        self.scanner = PortScanner()
        self.username, self.password = args
        self.counter = 0

    @asyncio.coroutine
    def scan(self):
        while True:
            print("Current Active cameras", self.active)
            tmp = self.scanner.scan(self.iprange)
            active_ip = [x[0] for x in self.active]
            for x in tmp:
                if x not in active_ip:
                    self.add(x)
            sleep(5)
            self.check_alive()

    def add(self, a):
        tmp = Camera(username=self.username, password=self.password, ip=a, tess=self.tess, backdrop=self)
        p = Process(target=tmp.start)
        self.active.add((a, p))
        p.start()

    def callback_tess(self, plate, image):
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2])
        self.cache(image)
        self.counter += 1

    def cache(self, image):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        ImagePreProcessing.save(image, filename)

    def callback_camera(self, ip):
        print("Removing camera", ip)
        self.active.discard(ip)

    def check_alive(self):
        tmp = self.active.copy()
        for process in tmp:
            if process[1].is_alive() is False:
                self.active.discard(process)
