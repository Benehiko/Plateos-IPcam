from threading import Thread

import cv2
import numpy as np

from Helper.ProcessHelper import ProcessHelper
from tess.tesseract import Tess


class Video:

    def __init__(self, filename):
        self.path = filename
        self.filename = ""
        self.set_name(filename)
        self.active = True
        self.frame = np.zeros([100, 100, 3], dtype=np.uint8)
        self.frame.fill(255)
        self.raw = np.zeros([100, 100, 3], dtype=np.uint8)
        self.raw.fill(255)
        self.processHelper = ProcessHelper()
        self.char = []
        self.char_raw = []
        self.tess = Tess()

    def start(self):

        while True:

            cap = cv2.VideoCapture(self.path)

            while cap.isOpened():
                if self.active is False:
                    break

                ret, frame = cap.read()
                if ret:
                    result, drawn, raw, chars = self.processHelper.analyse_frames(frame.copy())
                    if raw is not None:
                        self.raw = raw

                    if drawn is not None:
                        self.frame = drawn
                    else:
                        self.frame = frame

                    if chars is not None:
                        self.char = chars

                    if result is not None:
                        if len(result) > 0:
                            self.char_raw = result
                            t = Thread(self.tess.multi(result))
                            t.start()
                            t.join()

            cap.release()

    def set_active(self, val):
        self.active = val

    def get_name(self):
        return self.filename

    def set_name(self, filename):
        o = filename.split('/')
        self.filename = o[-1]

    def get_frame(self):
        return self.frame

    def get_raw_frame(self):
        return self.raw

    def get_char_frame(self):
        return self.char

    def get_char_raw(self):
        return self.char_raw
