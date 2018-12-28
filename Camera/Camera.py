import json
import random
import string
from datetime import datetime, timedelta
from urllib.request import urlopen

import cv2
import numpy as np

from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from Handlers.ThreadHandler import ThreadWithReturnValue
from Helper.ProcessHelper import ProcessHelper
from cvlib.ImageUtil import ImageUtil


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

        self.then = datetime.now()

    def start(self, q, q2):
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
                                t = ThreadWithReturnValue(target=self.tess.multi, args=(result,))
                                # t.daemon = True
                                t.start()
                                tmp = t.join()
                                if tmp is not None:
                                    tmp, meta = self.handle_data(tmp, img)
                                    if len(tmp) > 0:
                                        q.put(tmp)
                                    if len(meta) > 0:
                                        q2.put(meta)


            except Exception as e:
                print("Camera", self.get_camera_data()["alias"], self.get_camera_data()["ip"], "Died", "\nReason:", e)
                counter += 1
                if counter > 5:
                    break

    def handle_data(self, data, original_img):
        tmp = []
        meta = []

        results = [x for x in data if len(x) > 3]
        if len(results) > 0:
            tmp.append({"camera": self.mac, "results": results})

        now = datetime.now()
        diff = now - self.then
        if timedelta(minutes=5) < diff:
            allowed = [x for x in data if 5 <= x["char-len"] <= 8]
            image = ImageUtil.compress(original_img, max_w=1080, quality=100)
            if len(allowed) > 0:
                time = datetime.now().strftime('%Y-%m-%d %H:%M')
                meta.append({"camera": self.mac, "time": time, "original": image, "results": allowed})
            self.then = datetime.now()
        return tmp, meta

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
            print("Couldn't get Camera", self.ip, "mac", "\nReason:", e)
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
            print("Couldn't get Camera", self.ip, "information", "\nReason", e)
        return "", ""

    def get_camera_data(self):
        return dict([('mac', self.mac), ('alias', self.alias), ('ip', self.ip), ('model', self.model)])
