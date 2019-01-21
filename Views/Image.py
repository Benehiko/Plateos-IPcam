import cv2
import numpy as np

from Handlers.ThreadHandler import ThreadWithReturnValue
from Helper.ProcessHelper import ProcessHelper
from tess.tesseract import Tess


class Image:

    def __init__(self, filename):
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
        self.processHelper = ProcessHelper()
        self.tess = Tess()

    def start(self):
        img = cv2.imread(self.path, cv2.IMREAD_COLOR)
        self.frame = img
        while self.active:

            result, drawn, raw, chars = self.processHelper.analyse_frames(img.copy())
            if raw is not None:
                self.raw = raw

            if drawn is not None:
                self.frame = drawn
            else:
                self.frame = img

            if chars is not None:
                self.char = chars

            if result is not None:
                if len(result) > 0:
                    self.char_raw = result
                    t = ThreadWithReturnValue(target=self.tess.multi, args=(result,))
                    t.start()
                    self.data = t.join()

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

    def get_output(self):
        return self.data
