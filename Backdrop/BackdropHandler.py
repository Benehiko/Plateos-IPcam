import asyncio
import datetime
import pathlib
from multiprocessing import Process
from os import listdir
from os.path import isfile, join

from Caching.CacheHandler import CacheHandler
from DataHandler.PropertyHandler import PropertyHandler
from Network.PortScanner import PortScanner
from Network.requestor import Request
from camera.Camera import Camera
from numberplate.Numberplate import Numberplate
from tess.tesseract import Tess


class BackdropHandler:

    def __init__(self, backdrop):
        self.backdrop = backdrop

        # Scanner
        self.scanner = PortScanner()

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
            tmp = self.scanner.scan(PropertyHandler.app_settings["camera"]["iprange"], event_loop=event_loop)
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

            if datetime.timedelta(minutes=1) < diff:
                self.check_alive()
                old_time2 = datetime.datetime.now()

            if datetime.timedelta(minutes=30) < diff3:
                self.ping_location()
                old_time3 = datetime.datetime.now()
                
            if datetime.timedelta(hours=1) < diff2:
                self.cleanup_cache()
                self.offline_check()
                old_time2 = datetime.datetime.now()

    def callback_tess(self, plate):
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2], "Date:", plate[3])
        self.cached.append(plate)
        return

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

    def cache(self, c):
        try:
            today = datetime.datetime.now().strftime('%Y-%m-%d %H')
            c = Numberplate.improve(c)
            if c is not None:
                if len(c) > 0:
                    res = CacheHandler.save("cache", today, c)
                    if res is not None:
                        # print("Would have uploaded: ", res)
                        BackdropHandler.upload_dataset(res)
                        self.cached = []
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
                    CacheHandler.remove("cache/", file_last_date.strftime("%Y-%m-%d %H"))
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
                        tmp = CacheHandler.load("offline/", x).tolist()
                        Request.post(self.interface, tmp, self.url)
                        CacheHandler.remove("offline/", x)
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
