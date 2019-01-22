import cv2
import numpy as np

from Handlers.FrameHandler import FrameHandler
from Handlers.ThreadHandler import ThreadWithReturnValue
from Helper.ProcessHelper import ProcessHelper
from cvlib.CvHelper import CvHelper
from tess.tesseract import Tess


class Image:

    def __init__(self, filename, tess, cv_q):
        self.path = filename
        self.filename = ""
        self.set_name(filename)
        self.active = True
        self.frame = np.zeros([100, 100, 3], dtype=np.uint8)
        self.frame.fill(255)
        self.raw = np.zeros([100, 100, 3], dtype=np.uint8)
        self.raw.fill(255)
        self.char = []
        self.char_raw = []
        self.data = {}
        self.processHelper = ProcessHelper(cv_q)
        self.tess = tess

    def start(self):
        img = cv2.imread(self.path, cv2.IMREAD_COLOR)

        while self.active:
            self.frame = img
            result, self.frame, self.raw, chars = self.processHelper.analyse_frames(img.copy())

            if chars is not None:
                self.char = chars

            if result is not None:
                if len(result) > 0:
                    self.char_raw = result
                    t = ThreadWithReturnValue(target=self.tess.multi, args=(result,))
                    t.start()
                    self.data = t.join()
            if self.raw is None:
                print("raw null")
                self.raw = np.random.random([100, 100])
            FrameHandler.add_obj([self.filename, np.hstack((self.frame, CvHelper.gray2rgb(self.raw)))])

    def set_active(self, val):
        self.active = val

    def get_frame(self):
        return self.frame

    def get_raw_frame(self):
        return self.raw

    def get_name(self):
        return self.filename

    def set_name(self, filename):
        o = filename.split('/')
        self.filename = o[-1]

    def get_char_frame(self):
        return self.char

    def get_char_raw(self):
        return self.char_raw

    def get_ip(self):
        return self.filename
