import datetime
import pathlib
from multiprocessing import Process, Queue, Condition
from os import listdir
from os.path import isfile, join
from threading import Thread

from Camera.Camera import Camera
from Camera.CameraScan import CameraScan
from Handlers.CacheHandler import CacheHandler
from Handlers.NumberplateHandler import NumberplateHandler
from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from tess.tesseract import Tess


class BackdropHandler:

    def __init__(self):
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
        self.tess = Tess()

        self.cached = []
        self.active = set()
        self.old_time = datetime.datetime.now()

        self.cameras = []

        # Queues for File handling
        self.tmp_queue = Queue()
        self.meta_queue = Queue()
        self.cache_queue = Queue()

        # Flags for File handling
        self.tmp_access = True
        self.meta_access = True
        self.cache_access = True

        # Condition for File handling
        self.c_tmp = Condition()
        self.c_meta = Condition()
        self.c_cache = Condition()

    def start(self):
        old_time = datetime.datetime.now()
        old_time2 = datetime.datetime.now()
        old_time3 = datetime.datetime.now()

        while True:
            t = Thread(target=self.cache)
            t_tmp = Thread(target=self.tmp_queue_handler)
            t_meta = Thread(target=self.meta_queue_handler)
            t_cache = Thread(target=self.cache_queue_handler)
            t.start()
            t_tmp.start()
            t_meta.start()
            t_cache.start()
            active = self.active
            # print("Current Active cameras", active)
            tmp = self.scanner.scan(PropertyHandler.app_settings["camera"]["iprange"])
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
                t_cleanup = Thread(target=self.cleanup_cache)
                t_offline = Thread(target=self.offline_check)
                t_cleanup.start()
                t_offline.start()
                t_cleanup.join()
                t_offline.join()
                old_time2 = datetime.datetime.now()
            t.join()
            t_tmp.join()
            t_meta.join()
            t_cache.join()

    def add(self, ip):
        try:
            tmp = Camera(ip=ip, tess=self.tess)
            self.cameras.append(tmp)
            p = Process(target=tmp.start, args=(self.tmp_queue, self.meta_queue))
            self.active.add((ip, p))
            p.start()
        except Exception as e:
            print(e)
            pass

    def cache(self):
        """
        Do not add any extra tuple data to 'c'-plate data from tesseract
        Too much to edit in Numberplate.improve()
        """
        try:
            self.c_tmp.acquire()
            if self.tmp_access:
                self.tmp_access = False
                file_list = CacheHandler.get_file_list("tmp")
                tmp = []
                if len(file_list) > 0:
                    now = datetime.datetime.now()
                    for x in file_list:
                        data = CacheHandler.load("tmp", x)
                        if data is not None:
                            for d in data:
                                for y in d["results"]:
                                    diff = now - datetime.datetime.strptime(y["time"], '%Y-%m-%d %H:%M:%S')
                                    if datetime.timedelta(minutes=10) > diff:
                                        tmp.append((
                                            d["camera"], y["plate"], y["province"], y["confidence"], y["time"],
                                            y["image"]
                                        ))

                    file_last_date = datetime.datetime.strptime(min(file_list), "%Y-%m-%d %H:%M")
                    now = datetime.datetime.now()
                    diff = now - file_last_date
                    if datetime.timedelta(minutes=12) < diff:
                        CacheHandler.remove("tmp", file_last_date.strftime("%Y-%m-%d %H:%M"))

                    if len(tmp) > 0:
                        c = NumberplateHandler.improve([x[1:-1] for x in tmp])
                        if c is not None:
                            if len(c) > 0:
                                c = NumberplateHandler.remove_similar(c)
                                if c is not None:
                                    res = [x + (y[0],) for x in c for y in tmp if x[0] == y[1] and x[3] == y[4]]
                                    cache_data = [{"plate": x[0], "province": x[1], "confidence": x[2], "time": x[3], "camera": y[0], "image": y[5]} for x in c for y in tmp if
                                                  x[0] == y[1] and x[3] == y[4]]
                                    if len(res) > 0:
                                        self.upload_dataset(res)
                                        # print("Would have uploaded: ", res)
                                        pass
                                    if len(cache_data) > 0:
                                        self.c_cache.acquire()
                                        if self.cache_access:
                                            self.cache_access = False
                                            self.cache_queue.put(cache_data)
                                            self.cache_access = True
                                            self.c_cache.notify_all()
                                        else:
                                            self.c_cache.wait()
                                        self.c_cache.release()

                self.tmp_access = True
                self.c_tmp.notify_all()
            else:
                self.c_tmp.wait()
            self.c_tmp.release()


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
        self.c_cache.acquire()
        if self.cache_access:
            self.cache_access = False
            try:
                pathlib.Path("cache").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("cache")
                if len(files) > 0:
                    file_last_date = datetime.datetime.strptime(min(files), "%Y-%m-%d %H")
                    now = datetime.datetime.now()
                    diff = now - file_last_date
                    if datetime.timedelta(days=60) < diff:
                        CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
            except Exception as e:
                print("Error on Cleaning Cache", e)
                pass
            self.cache_access = True
            self.c_cache.notify_all()
        else:
            self.c_cache.wait()
        self.c_cache.release()

        self.c_meta.acquire()
        if self.meta_access:
            self.meta_access = False
            try:
                pathlib.Path("meta").mkdir(parents=True, exist_ok=True)
                files = [f.replace('.npz', '') for f in listdir("meta") if isfile(join("meta", f))]
                if len(files) > 0:
                    for x in files:
                        file_last_date = datetime.datetime.strptime(x, "%Y-%m-%d %H:%M")
                        now = datetime.datetime.now()
                        diff = now - file_last_date
                        if datetime.timedelta(days=20) < diff:
                            CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
            except Exception as e:
                print("Error on Cleaning Meta", e)
                pass
            self.meta_access = True
            self.c_meta.notify_all()
        else:
            self.c_meta.wait()
        self.c_meta.release()

    def offline_check(self):
        if Request.check_connectivity():
            try:
                pathlib.Path("offline").mkdir(parents=True, exist_ok=True)
                files = [f.replace('.npz', '') for f in listdir("offline") if isfile(join("offline", f))]
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

    def tmp_queue_handler(self):
        self.c_tmp.acquire()
        if self.tmp_access:
            self.tmp_access = False
            while not self.tmp_queue.empty():
                val = self.tmp_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    CacheHandler.save_tmp("tmp", now, val)
            self.tmp_access = True
            self.c_tmp.notify_all()
        else:
            self.c_tmp.wait()
        self.c_tmp.release()

    def meta_queue_handler(self):
        self.c_meta.acquire()
        if self.meta_access:
            self.meta_access = False
            while not self.meta_queue.empty():
                val = self.meta_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    CacheHandler.save_meta("meta", now, val)
            self.meta_access = True
            self.c_meta.notify_all()
        else:
            self.c_meta.wait()
        self.c_meta.release()

    def cache_queue_handler(self):
        self.c_cache.acquire()
        if self.cache_access:
            self.cache_access = False
            while not self.cache_queue.empty():
                val = self.cache_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H')
                    CacheHandler.save_cache("cache", now, val)
            self.cache_access = True
            self.c_cache.notify_all()
        else:
            self.c_cache.wait()
        self.c_cache.release()
