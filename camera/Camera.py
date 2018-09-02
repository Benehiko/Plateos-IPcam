import asyncio
import random
import string
from threading import Thread
from time import sleep
from urllib.request import urlopen

import cv2
import numpy as np

from Helper.ProcessHelper import ProcessHelper


class Camera:

    def __init__(self, ip, username, password, tess, backdrop):
        randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.url = "http://" + ip + "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=" + randomcmd + "&user=" + username + "&password=" + password
        # self.url = "rtsp://"+username+":"+password+"@"+ip+":554//h264Preview_01_main"
        # self.url = "rtmp://" + ip + "/bcs/channel0_main.bcs?channel=0&stream=0&user=" + username + "&password=" + password
        self.tess = tess
        self.ip = ip
        self.backdrop = backdrop
        self.loop = asyncio.get_event_loop()
        self.historic = []

    def start(self):
        print("Starting camera", self.ip)
        while True:
            try:
                frames = []
                for i in range(0, 5):
                    reader = urlopen(self.url, timeout=10)
                    if reader.status == 200:
                        img_npy = np.array(bytearray(reader.read()), dtype=np.uint8)
                        img = cv2.imdecode(img_npy, -1)
                        frames.append(img)
                    sleep(0.5)

                cropped_array, historic_array = ProcessHelper.analyse_frames(self.historic, frames)

                if cropped_array is not None:
                    self.historic = historic_array

                    if len(cropped_array) > 0:
                        t = Thread(target=self.tess.multi(cropped_array))
                        t.start()
                        t.join(5)

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cv2.destroyWindow(self.ip)
                    break
                else:
                    break

            except Exception as e:
                print(e)
                break

            finally:
                sleep(1)
                pass

        self.backdrop.callback_camera(self.ip)
