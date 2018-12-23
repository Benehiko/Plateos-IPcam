import json
import random
import string
from threading import Thread
from time import sleep
from urllib.request import urlopen

import cv2
import numpy as np

from DataHandler.PropertyHandler import PropertyHandler
from Helper.ProcessHelper import ProcessHelper
from Network.requestor import Request


class Camera:

    def __init__(self, ip, tess):
        self.randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        self.tess = tess
        self.ip = ip
        self.rest = PropertyHandler.app_settings["camera"]["restful"]
        self.username = PropertyHandler.app_settings["camera"]["username"]
        self.password = PropertyHandler.app_settings["camera"]["password"]
        self.processHelper = ProcessHelper()
        self.mac = self.get_mac()
        self.alias, self.model = self.get_info()
        self.url = "http://" + ip + self.rest["base"] + "cmd=" + self.rest["snap"]["cmd"] + "&channel=" + str(
            self.rest["snap"][
                "channel"]) + "&rs=" + self.randomcmd + "&user=" + \
                   self.username + "&password=" + self.password

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
                        result, __, __, __ = self.processHelper.analyse_frames(img)

                        if result is not None:
                            if len(result) > 0:
                                t = Thread(self.tess.multi(result, self.mac, img))
                                t.start()
                                t.join()

            except Exception as e:
                print("Camera", self.get_camera_data()["alias"], self.get_camera_data()["ip"], "Died", "\nReason:", e)
                break

    def get_mac(self):
        try:
            params = [('cmd', self.rest["mac"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                      ('password', self.password)]
            url = "http://" + self.ip + self.rest["base"]
            data = Request.get(url, params)
            j = json.loads(data)
            mac = j[0]['value']['LocalLink']['mac']
            return mac
        except Exception as e:
            print("Couldn't get camera", self.ip, "mac", "\nReason:", e)

    def get_info(self):
        try:
            params = [('cmd', self.rest["info"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                      ('password', self.password)]
            url = "http://" + self.ip + self.rest["base"]
            data = Request.get(url, params)
            j = json.loads(data)
            alias = j[0]["value"]["DevInfo"]["name"]
            model = j[0]["value"]["DevInfo"]["model"]
            return alias, model
        except Exception as e:
            print("Couldn't get camera", self.ip, "information", "\nReason", e)

    def get_camera_data(self):
        return dict([('mac', self.mac), ('alias', self.alias), ('ip', self.ip), ('model', self.model)])
