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
from Handlers.ThreadHandler import ThreadWithReturnValue
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
            t_tmp = Thread(target=self.tmp_queue_handler, args=(self.c_tmp,))
            t_meta = Thread(target=self.meta_queue_handler, args=(self.c_meta,))
            t_cache = Thread(target=self.cache_queue_handler, args=(self.c_cache,))
            t_tmp.start()
            t_meta.start()
            t_cache.start()


            active = self.active

            # print("Current Active cameras", active)
            t_camera = ThreadWithReturnValue(target=self.scanner.scan,
                                             args=(PropertyHandler.app_settings["camera"]["iprange"],))
            t_camera.start()

            # Use timedelta
            """Time delta to run certain checks periodically"""
            now = datetime.datetime.now()
            diff = now - old_time
            diff2 = now - old_time2
            diff3 = now - old_time3

            if datetime.timedelta(seconds=10) < diff:
                self.check_alive()
                t_cleanup = Thread(target=self.cleanup_cache, args=(self.c_cache, self.c_meta, self.c_tmp,))
                t_cleanup.start()
                t_cleanup.join()
                old_time = datetime.datetime.now()

            if datetime.timedelta(minutes=30) < diff3:
                Thread(target=self.ping_location).start()
                old_time3 = datetime.datetime.now()

            if datetime.timedelta(minutes=10) < diff2:
                t_offline = Thread(target=self.offline_check)
                t_offline.start()
                t_offline.join()
                old_time2 = datetime.datetime.now()

            found_camera = t_camera.join()
            active_ip = [x[0] for x in active]
            if len(found_camera) > 0:
                for x in found_camera:
                    if x not in active_ip:
                        self.add(x)
                        self.add(x)
            t_tmp.join()
            t_meta.join()
            t_cache.join()

            # Do not change the position of self.cache thread (it's put here intentionally).
            t = Thread(target=self.cache, args=(self.c_tmp, self.c_cache,))
            t.start()
            t.join()

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

    def cache(self, cv_tmp: Condition, cv_cache: Condition):
        """
        Extract numberplate from tmp directory and build confidence based off of tmp files.
        Once confidence is built, compare to existing cache data, remove duplications and upload (only if data is 2 min newer than cache)
        If cache does not contain such data, upload the file regardless of waiting time (2min).
        Save to cache.
        """
        try:
            def time_key(item):
                return datetime.datetime.strptime(item[4], "%Y-%m-%d %H:%M:%S")

            with cv_tmp:
                file_list = CacheHandler.get_file_list("tmp")
                tmp = []
                if len(file_list) > 0:
                    for x in file_list:
                        data = CacheHandler.load("tmp", x)
                        if data is not None:
                            for d in data:
                                for y in d["results"]:
                                    tmp.append((
                                        d["camera"], y["plate"], y["province"], y["confidence"], y["time"],
                                        y["image"]
                                    ))

                    if len(tmp) > 0:
                        c = NumberplateHandler.improve([x[1:-1] for x in tmp])
                        if c is not None:
                            if len(c) > 0:
                                c = NumberplateHandler.remove_similar(c)
                                if c is not None:
                                    with cv_cache:
                                        res = [x + (y[0],) for x in c for y in tmp if x[0] == y[1] and x[3] == y[4]]
                                        if len(res) > 0:
                                            upload_list = []
                                            cache_res = []
                                            for x in res:
                                                cache_res += CacheHandler.loadByPlate("cache",
                                                                                      datetime.datetime.now().strftime(
                                                                                          "%Y-%m-%d %H"), x[0])
                                            if len(cache_res) > 0:
                                                for x in cache_res:
                                                    t = [y for y in tmp if
                                                         y[1] == x["plate"]]
                                                    m_t = max(t, key=lambda p: time_key(p))

                                                    if len(m_t) > 0:
                                                        diff = datetime.datetime.strptime(m_t[4],
                                                                                          "%Y-%m-%d %H:%M:%S") - datetime.datetime.strptime(
                                                            x["time"],
                                                            "%Y-%m-%d %H:%M:%S")
                                                        if datetime.timedelta(minutes=4) > diff > datetime.timedelta(
                                                                minutes=2):
                                                            new_conf = [p for p in res if p[0] == m_t[1]]
                                                            if len(new_conf) > 0:
                                                                if (new_conf[0][2] -
                                                                    PropertyHandler.numberplate["Confidence"][
                                                                        "min-deviation"]) > 0.5:
                                                                    upload_list += [
                                                                        (
                                                                            m_t[1], m_t[2], new_conf[0][2], m_t[4],
                                                                            m_t[0])]
                                            else:
                                                upload_list += res
                                            if len(upload_list) > 0:
                                                self.upload_dataset(res)
                                                # print("Would have uploaded: ", upload_list)

                                                cache_data = [
                                                    {"plate": x[0], "province": x[1], "confidence": x[2], "time": x[3],
                                                     "camera": y[0], "image": y[5]} for x in upload_list for y in tmp if
                                                    x[0] == y[1] and x[3] == y[4]]

                                                if len(cache_data) > 0:
                                                    self.cache_queue.put(cache_data)
                                        cv_cache.notify_all()
                cv_tmp.notify_all()

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
    def cleanup_cache(self, cv_cache: Condition, cv_meta: Condition, cv_tmp: Condition):
        with cv_cache:
            try:
                pathlib.Path("cache").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("cache")
                if len(files) > 0:
                    for x in files:
                        file_last_date = datetime.datetime.strptime(x, "%Y-%m-%d %H")
                        now = datetime.datetime.now()
                        diff = now - file_last_date
                        if datetime.timedelta(days=90) <= diff:
                            CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
            except Exception as e:
                print("Error on Cleaning Cache", e)
                pass
            cv_cache.notify_all()

        with cv_meta:
            try:
                pathlib.Path("meta").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("meta")
                if len(files) > 0:
                    now = datetime.datetime.now()
                    for x in files:
                        file_last_date = datetime.datetime.strptime(x, "%Y-%m-%d %H:%M")
                        diff = now - file_last_date
                        if datetime.timedelta(days=20) <= diff:
                            CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
            except Exception as e:
                print("Error on Cleaning Meta", e)
                pass
            cv_meta.notify_all()

        with cv_tmp:
            try:
                pathlib.Path("tmp").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("tmp")
                if len(files) > 0:
                    now = datetime.datetime.now()
                    for x in files:
                        diff = now - datetime.datetime.strptime(x, "%Y-%m-%d %H:%M")
                        if datetime.timedelta(minutes=10) <= diff:
                            CacheHandler.remove("tmp", x)
            except Exception as e:
                print("Error on Cleaning tmp", e)
                pass
            cv_tmp.notify_all()

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

    def tmp_queue_handler(self, cv: Condition):
        with cv:
            while not self.tmp_queue.empty():
                val = self.tmp_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    CacheHandler.save_tmp("tmp", now, val)
            cv.notify_all()

    def meta_queue_handler(self, cv: Condition):
        with cv:
            while not self.meta_queue.empty():
                val = self.meta_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                    CacheHandler.save_meta("meta", now, val)
            cv.notify_all()

    def cache_queue_handler(self, cv: Condition):
        with cv:
            while not self.cache_queue.empty():
                val = self.cache_queue.get()
                if val is not None:
                    now = datetime.datetime.now().strftime('%Y-%m-%d %H')
                    CacheHandler.save_cache("cache", now, val)
            cv.notify_all()
