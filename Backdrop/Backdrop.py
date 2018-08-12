from camera.Camera import Camera
from multiprocessing import Process
from tess.tesseract import Tess
from cvShapeHandler.imageprocessing import ImagePreProcessing
from numberplate.Numberplate import Numberplate

import datetime


class Backdrop:

    def __init__(self, args):
        (username, password, ip) = args
        self.camera = []
        self.tess = Tess(backdrop=self)
        for addr in ip:
            self.camera.append(Camera(username=username, password=password, ip=addr, tess=self.tess))

        self.plates = []
        self.counter = 0

    def run(self):
        pool = []
        for cam in self.camera:
            pool.append(Process(target=cam.start))

        for i in range(0, len(pool)):
            pool[i].start()

        for i in range(0, len(pool)):
            pool[i].join()

    def callback_tess(self, plate):
        #if self.counter == 20:
            #plates = Numberplate.improve(self.plates)
            #if len(plates) > 0:
                #self.cache(plates)
            #self.counter = 0
            #self.plates = []

        #plate = [x for x in plate if x is not None]  # Keep element if it is not None
        self.plates.append(plate)
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:",plate[2])
        self.cache(plate)
        self.counter += 1

    def cache(self, plate):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        ImagePreProcessing.save(plate[3], filename)
