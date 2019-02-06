import asyncio
import json
import random
import string
from datetime import datetime
from multiprocessing import Queue
from time import sleep
from urllib.request import urlopen

import cv2
import janus
import numpy as np

from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from cvlib.ImageUtil import ImageUtil


class Camera:

    def __init__(self, ip):
        self.randomcmd = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.ip = ip
        self.rest = PropertyHandler.app_settings["camera"]["restful"]
        self.username = PropertyHandler.app_settings["camera"]["username"]
        self.password = PropertyHandler.app_settings["camera"]["password"]
        self.seconds_per_frame = PropertyHandler.app_settings["camera"]["seconds-per-frame"]
        self.mac = self.get_mac()
        self.alias, self.model = self.get_info()
        self.url = "http://" + ip + self.rest["base"] + "cmd=" + self.rest["snap"]["cmd"] + "&channel=" + str(
            self.rest["snap"][
                "channel"]) + "&rs=" + self.randomcmd + "&user=" + \
                   self.username + "&password=" + self.password

        self.then = datetime.now()
        self.frame = np.zeros([100, 100, 3], dtype=np.uint8)
        self.frame.fill(255)
        self.raw = np.zeros([100, 100, 3], dtype=np.uint8)
        self.raw.fill(255)
        self.data = []
        self.framequeue = Queue()

    async def start(self, q_frames: janus.Queue.async_q):
        if self.mac == "":
            return

        print("Starting Camera:\nIP:", self.ip, "MAC:", self.mac, "Model", self.model)
        while True:
            try:
                reader = urlopen(self.url, timeout=3)
                if reader.status == 200:
                    b = bytearray(reader.read())
                    npy = np.array(b, dtype=np.uint8)
                    img = cv2.imdecode(npy, -1)
                    if img is not None:
                        if self.model == "" or self.alias == "":
                            self.model, self.alias = self.get_info()
                        q_frames.put_nowait({"mac": self.mac, "ip": self.ip, "image": img})
                sleep(self.seconds_per_frame)
            except Exception as e:
                print("Camera", self.get_camera_data()["alias"], self.get_camera_data()["ip"], "Died")
                await asyncio.sleep(1)

    def handle_data(self, data, original_img):
        tmp = []
        meta = []

        results = [x for x in data if len(x) > 3]
        if len(results) > 0:
            tmp.append({"camera": self.mac, "results": results})

        # now = datetime.now()
        # diff = now - self.then
        # if timedelta(minutes=5) < diff:
        allowed = [x for x in data if 3 <= x["char-len"] <= 8]
        image = ImageUtil.compress(original_img, max_w=1080, quality=100)
        if len(allowed) > 0:
            time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            meta.append({"camera": self.mac, "time": time, "original": image, "results": allowed})
        # self.then = datetime.now()
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

    def get_frame(self):
        return self.frame

    def get_name(self):
        return self.get_mac()

    def get_raw_frame(self):
        return self.raw

    def get_output(self):
        return self.data

    def get_ip(self):
        return self.ip
