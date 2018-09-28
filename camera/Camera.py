import random
import string
from urllib.request import urlopen

import cv2
import numpy as np

from Helper.ProcessHelper import ProcessHelper


class Camera:

    def __init__(self, ip, username, password, tess, backdrop):
        randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.url = "http://" + ip + "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=" + randomcmd + "&user=" + username + "&password=" + password
        self.tess = tess
        self.ip = ip
        self.backdrop = backdrop

    def start(self):
        print("Starting camera", self.ip)
        counter = 0
        while True:
            try:
                reader = urlopen(self.url, timeout=2)
                if reader.status == 200:
                    if counter > 5:
                        counter = 0
                        b = bytearray(reader.read())
                        npy = np.array(b, dtype=np.uint8)
                        img = cv2.imdecode(npy, -1)
                        if img is not None:
                            cropped_array = ProcessHelper.analyse_frames(img)

                            if cropped_array is not None:
                                if len(cropped_array) > 0:
                                    self.tess.multi(cropped_array)
                    counter += 1

            except:
                pass

            finally:
                pass
