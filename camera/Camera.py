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
        if self.mac == "":
            for i in range(0, 5):
                if self.mac == "":
                    if i < 5:
                        self.mac = self.get_mac()
                    else:
                        return
                else:
                    break
        if self.alias or self.model == "":
            for i in range(0, 5):
                if self.alias or self.model == "":
                    if i < 5:
                        self.alias, self.model = self.get_info()
                    else:
                        return
                else:
                    break
        print("Starting Camera:\nIP:", self.ip, "MAC:", self.mac, "Model", self.model)
        counter = 0
        while True:
            try:
                reader = urlopen(self.url, timeout=1)
                if reader.status == 200:
                    counter = 0
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
                counter += 1
                if counter > 5:
                    break

    def get_mac(self):
        try:
            params = [('cmd', self.rest["mac"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                      ('password', self.password)]
            url = "http://" + self.ip + self.rest["base"]
            data = Request.get(url, params)
            if data is not None:
                j = json.loads(data)
                mac = j[0]['value']['LocalLink']['mac']
                return mac
        except Exception as e:
            print("Couldn't get camera", self.ip, "mac", "\nReason:", e)
            pass
        return ""

    def get_info(self):
        try:
            params = [('cmd', self.rest["info"]["cmd"]), ('rs', self.randomcmd), ('user', self.username),
                      ('password', self.password)]
            url = "http://" + self.ip + self.rest["base"]
            data = Request.get(url, params)
            if data is not None:
                j = json.loads(data)
                alias = j[0]["value"]["DevInfo"]["name"]
                model = j[0]["value"]["DevInfo"]["model"]
                return alias, model
        except Exception as e:
            print("Couldn't get camera", self.ip, "information", "\nReason", e)
        return "", ""

    def get_camera_data(self):
        return dict([('mac', self.mac), ('alias', self.alias), ('ip', self.ip), ('model', self.model)])
