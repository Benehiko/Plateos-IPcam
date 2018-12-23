import asyncio
import datetime
import pathlib
from multiprocessing import Process
from os import listdir
from os.path import isfile, join

from Caching.CacheHandler import CacheHandler
from DataHandler.PropertyHandler import PropertyHandler
from Network.CameraScan import CameraScan
from Network.requestor import Request
from camera.Camera import Camera
from numberplate.NumberplateHandler import NumberplateHandler
from tess.tesseract import Tess


class BackdropHandler:

    def __init__(self, backdrop):
        self.backdrop = backdrop

        # Scanner
        self.scanner = CameraScan()

        # Device
        device = PropertyHandler.app_settings["device"]
        self.alias = device["alias"]
        self.interface = device["interface"]

        # Restful Service
        restful = PropertyHandler.app_settings["restful"]
        self.port = restful["port"]
        self.url = restful["url"] + ":" + str(self.port)
        self.addplate = restful["addplate"]
        self.addlocation = restful["addlocation"]

        # Tesseract init
        self.tess = Tess(backdrop=self)

        self.cached = []
        self.active = set()
        self.old_time = datetime.datetime.now()

        self.cameras = []

    def start(self):
        old_time = datetime.datetime.now()
        old_time2 = datetime.datetime.now()
        old_time3 = datetime.datetime.now()

        while True:
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)
            active = self.active
            # print("Current Active cameras", active)
            tmp = self.scanner.scan(PropertyHandler.app_settings["camera"]["iprange"])
            event_loop.close()
            active_ip = [x[0] for x in active]
            for x in tmp:
                if x not in active_ip:
                    self.add(x)

            # Use timedelta
            """Time delta to run certain checks periodically"""
            now = datetime.datetime.now()
            diff = now - old_time
            diff2 = now - old_time2
            diff3 = now - old_time3

            if datetime.timedelta(seconds=10) < diff:
                self.check_alive()
                old_time = datetime.datetime.now()

            if datetime.timedelta(minutes=30) < diff3:
                self.ping_location()
                old_time3 = datetime.datetime.now()

            if datetime.timedelta(hours=1) < diff2:
                self.cleanup_cache()
                self.offline_check()
                old_time2 = datetime.datetime.now()

    def add(self, ip):
        try:
            tmp = Camera(ip=ip, tess=self.tess)
            self.cameras.append(tmp)
            p = Process(target=tmp.start)
            self.active.add((ip, p))
            p.start()
        except Exception as e:
            print(e)
            pass

    def cache(self, c, camera_mac):
        """
        Do not add any extra tuple data to 'c'-plate data from tesseract
        Too much to edit in Numberplate.improve()
        """
        try:
            if len(c) > 0:
                today = datetime.datetime.now().strftime('%Y-%m-%d %H')
                tmp = []
                for x in c:
                    tmp.append((x["plate"], x["province"], x["confidence"], x["time"], x["image"]))
                c = tmp
                c = NumberplateHandler.improve(c)
                if c is not None:
                    if len(c) > 0:
                        c = NumberplateHandler.remove_similar(c)
                        res = CacheHandler.save("cache", today, c)
                        if res is not None:
                            # print("Would have uploaded: ", res)
                            res = [x + (camera_mac,) for x in res]
                            self.upload_dataset(res)
        except Exception as e:
            print(e)
            pass

    def check_alive(self):
        tmp = self.active.copy()
        for process in tmp:
            try:
                if process[1].is_alive() is False:
                    self.active.discard(process)
            except Exception as e:
                print("Tried to remove process", e)

    def upload_dataset(self, data):
        try:
            url = "http://" + self.url + self.addplate
            Request.post(self.interface, data, url)
        except Exception as e:
            print(e)
            pass

    # noinspection PyMethodMayBeStatic
    def cleanup_cache(self):
        try:
            pathlib.Path("cache").mkdir(parents=True, exist_ok=True)
            files = [f.replace('.npy.gz', '') for f in listdir("cache") if isfile(join("cache", f))]
            if len(files) > 0:
                file_last_date = datetime.datetime.strptime(max(files), "%Y-%m-%d %H")
                now = datetime.datetime.now()
                diff = now - file_last_date
                if datetime.timedelta(days=90) < diff:
                    CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
            pathlib.Path("meta").mkdir(parents=True, exist_ok=True)
            files = [f.replace('.npy.gz', '') for f in listdir("meta") if isfile(join("meta", f))]
            if len(files) > 0:
                for x in files:
                    file_last_date = datetime.datetime.strptime(x, "%Y-%m-%d %H:%M")
                    now = datetime.datetime.now()
                    diff = now - file_last_date
                    if datetime.timedelta(days=20) < diff:
                        CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
        except Exception as e:
            print(e)
            pass

    def offline_check(self):
        if Request.check_connectivity():
            try:
                pathlib.Path("offline").mkdir(parents=True, exist_ok=True)
                files = [f.replace('.npy.gz', '') for f in listdir("offline") if isfile(join("offline", f))]
                if len(files) > 0:
                    for x in files:
                        tmp = CacheHandler.load("offline", x).tolist()
                        if tmp is not None:
                            Request.post(self.interface, tmp, self.url)
                            CacheHandler.remove("offline", x)
            except Exception as e:
                print(e)
                pass

    def ping_location(self):
        try:
            if Request.check_connectivity():
                url = "http://" + self.url + self.addlocation
                camdata = []
                for cam in self.cameras:
                    camdata.append(cam.get_camera_data())
                Request.ping_location(self.interface, url, self.alias, camdata)
        except Exception as e:
            print(e)
            pass

    def tess_save_meta(self, data):
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        CacheHandler.save_meta("meta", now, data)
