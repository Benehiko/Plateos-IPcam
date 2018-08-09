from camera.Camera import Camera
from multiprocessing import Process
from tess.tesseract import Tess

class Backdrop:

    def __init__(self, args):
        (username, password, ip) = args
        self.camera = []
        self.tess = Tess(backdrop=self)
        for addr in ip:
            self.camera.append(Camera(username=username, password=password, ip=addr, tess=self.tess))



    def run(self):
        pool = []
        for cam in self.camera:
            pool.append(Process(target=cam.start))

        for i in range(0, len(pool)):
            pool[i].start()

        for i in range(0, len(pool)):
            pool[i].join()

    def callbackPlate(self, plate):
        plate = [x for x in plate if x is not None]  # Keep element if it is not False
        print(plate)
