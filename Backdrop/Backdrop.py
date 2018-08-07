
class Backdrop:

    def __init__(self, *args):
        self.camera = []
        for c in args:
            self.camera.append(c)

    def run(self):
        for cam in self.camera:
            cam.start()
