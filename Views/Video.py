from time import sleep

import cv2
import janus
import numpy as np


class Video:

    def __init__(self, filename):
        self.base = "/mnt/data/SoftwareDevelopment/GitHub/plateos-files/videos/"
        self.path = self.base + filename
        self.filename = ""
        self.set_name(filename)
        self.active = True
        self.frame = np.zeros([100, 100, 3], dtype=np.uint8)
        self.frame.fill(255)
        self.raw = np.zeros([100, 100, 3], dtype=np.uint8)
        self.raw.fill(255)
        self.char = []
        self.char_raw = []

    def start(self, q_frames: janus.Queue.sync_q):
        print("Starting Video")
        while True:

            cap = cv2.VideoCapture(self.path)

            while cap.isOpened():
                if self.active is False:
                    break

                ret, frame = cap.read()
                if ret:
                    q_frames.put_nowait({"mac": self.filename, "ip": self.filename, "image": frame})
                sleep(1)
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

    def get_camera_data(self):
        return dict([('mac', self.filename), ('alias', 'VideoFeed'), ('ip', self.filename), ('model', 'V1')])

    def get_info(self):
        return 'VideoFeed', 'V1'
