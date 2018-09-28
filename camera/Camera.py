import random
import string
from threading import Thread
from urllib.error import URLError
from urllib.request import urlopen

import cv2
import numpy as np

from Helper.ProcessHelper import ProcessHelper


class Camera:

    def __init__(self, ip, username, password, tess):
        randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.url = "http://" + ip + "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=" + randomcmd + "&user=" + username + "&password=" + password
        self.tess = tess
        self.ip = ip

    def start(self):
        print("Starting camera", self.ip)
        while True:
            try:
                reader = urlopen(self.url, timeout=5)
                if reader.status == 200:
                        b = bytearray(reader.read())
                        npy = np.array(b, dtype=np.uint8)
                        img = cv2.imdecode(npy, -1)
                        if img is not None:
                            cropped_array = ProcessHelper.analyse_frames(img)

                            if cropped_array is not None:
                                if len(cropped_array) > 0:
                                    t = Thread(self.tess.multi(cropped_array))
                                    t.start()
                                    t.join(timeout=10)

            except:
                pass
