from camera.Camera import Camera
from multiprocessing import Process
from tess.tesseract import Tess
from cvShapeHandler.imageprocessing import ImagePreProcessing
from numberplate.Numberplate import Numberplate
from Network.PortScanner import PortScanner

import datetime


class Backdrop:

    def __init__(self):
        self.camera = []
        self.tess = Tess(backdrop=self)

        self.plates = []
        self.counter = 0
        self.pool = []
        self.scanner = PortScanner()

    def run(self, args):
        (username, password) = args

        while True:
            active = self.scanner.scan("192.168.1.100-192.168.1.200")
            a = [x for x in active if x not in self.pool]
            for addr in a:
                self.threader(username, password, addr)

    def callback_tess(self, plate):
        # if self.counter == 10:
        #     Numberplate.improve(self.plates)
        #     self.counter = 0
        #     self.plates = []

        #plate = [x for x in plate if x is not None]  # Keep element if it is not None
        #self.plates.append(plate)
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2])
        self.cache(plate)
        self.counter += 1

    def cache(self, plate):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        ImagePreProcessing.save(plate[3], filename)

    def callback_camera(self, camera_id):
        del self.pool[self.pool.index(camera_id)]

    def threader(self, username, password, ip):
        self.pool.append(ip)
        tmp = Camera(username=username, password=password, ip=ip, tess=self.tess, backdrop=self)
        p = Process(target=tmp.start)
        p.start()
        p.join()
