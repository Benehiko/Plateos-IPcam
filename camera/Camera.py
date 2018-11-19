import json
import random
import string
from threading import Thread
from time import sleep
from urllib.request import urlopen

import cv2
import numpy as np

from Helper.ProcessHelper import ProcessHelper
from Network.requestor import Request


class Camera:

    def __init__(self, ip, rest, credentials, tess):
        self.randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.url = "http://" + ip + rest["base"] + "cmd=" + rest["snap"]["cmd"] + "&channel=" + str(rest["snap"][
                                                                                                        "channel"]) + "&rs=" + self.randomcmd + "&user=" + \
                   credentials["username"] + "&password=" + credentials[
                       "password"]

        self.tess = tess
        self.ip = ip
        self.rest = rest
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.mac = self.get_mac()
        self.alias, self.model = self.get_info()

    def start(self):
        print("Starting Camera:\nIP:", self.ip, "MAC:", self.mac, "Model", self.model)
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
                                t.join()

            except Exception as e:
                print("Camera died", e)
                sleep(1)
                pass

    def get_mac(self):
        params = [('cmd', self.rest["mac"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                  ('password', self.password)]
        url = "http://" + self.ip + self.rest["base"]
        data = Request.get(url, params)
        j = json.loads(data)
        mac = j[0]['value']['LocalLink']['mac']
        return mac

    def get_info(self):
        params = [('cmd', self.rest["info"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                  ('password', self.password)]
        url = "http://" + self.ip + self.rest["base"]
        data = Request.get(url, params)
        j = json.loads(data)
        alias = j[0]["value"]["DevInfo"]["name"]
        model = j[0]["value"]["DevInfo"]["model"]
        return alias, model

    def get_camera_data(self):
        return dict([('mac', self.mac), ('alias', self.alias), ('ip', self.ip), ('model', self.model)])
