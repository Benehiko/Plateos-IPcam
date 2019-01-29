from datetime import datetime, timedelta
import pathlib
from multiprocessing import Process, Queue, Condition
from os import listdir
from os.path import isfile, join
from threading import Thread

from Handlers.FrameHandler import FrameHandler
from Views.Camera import Camera
from Camera.CameraScan import CameraScan
from Handlers.CacheHandler import CacheHandler
from Handlers.CachedNumberplateHandler import CachedNumberplateHandler
from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from Handlers.ThreadHandler import ThreadWithReturnValue
from tess.tesseract import Tess


class BackdropHandler:

    # TODO: Add type mapping and return types to methods with correct descriptions

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
        self.cameras = set()
        self.old_time = datetime.now()

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
        self.c_upload = Condition()

        self.meta_time = Queue()
        self.meta_time.put(datetime.now())
        self.camera_queue = None
        self.cv_q = None

    def start(self, queue, cv_q):
        self.camera_queue = queue
        self.cv_q = cv_q

        event_time = event_time2 = event_time3 = event_time4 = datetime.now()

        while True:
            t_tmp = Thread(target=self.tmp_queue_handler, args=(self.c_tmp,))
            t_meta = Thread(target=self.meta_queue_handler, args=(self.c_meta, self.meta_time))
            t_cache = Thread(target=self.cache_queue_handler, args=(self.c_cache,))
            t_tmp.start()
            t_meta.start()
            t_cache.start()

            # print("Current Active cameras", active)
            t_camera = ThreadWithReturnValue(target=self.scanner.scan,
                                             args=(PropertyHandler.app_settings["camera"]["iprange"],))
            t_camera.start()

            # Use timedelta
            """Time delta to run certain checks periodically"""
            now = datetime.now()
            diff = now - event_time
            diff2 = now - event_time2
            diff3 = now - event_time3
            diff4 = now - event_time4

            if timedelta(seconds=10) < diff:
                self.check_alive()
                # Clean Gui Images
                t_gui = Thread(target=FrameHandler.clean)
                t_gui.start()
                found_camera = t_camera.join()
                if len(found_camera) > 0:
                    for x in found_camera:
                        self.add(x)
                t_gui.join()
                event_time = datetime.now()

            if timedelta(minutes=1) < diff2:
                ping_thread = Thread(target=self.ping_location)
                tmp_cleanup = Thread(target=self.cleanup_temp, args=(self.c_tmp,))
                ping_thread.start()
                tmp_cleanup.start()
                ping_thread.join()
                tmp_cleanup.join()
                event_time2 = datetime.now()

            if timedelta(minutes=10) < diff3:
                t_offline = Thread(target=self.offline_check)
                t_offline.start()
                t_offline.join()
                event_time3 = datetime.now()

            if timedelta(hours=20) < diff4:
                t_cleanup = Thread(target=self.cleanup_cache,
                                   args=(self.c_cache, self.c_meta, self.c_upload,))
                t_cleanup.start()
                t_cleanup.join()
                event_time4 = datetime.now()

            t_tmp.join()
            t_meta.join()
            t_cache.join()

            # Do not change the position of self.cache thread (it's put here intentionally).
            t = Thread(target=self.cache, args=(self.c_tmp, self.c_cache, self.c_upload,))
            t.start()
            t.join()

    def add(self, ip):
        try:

            for x in self.cameras:
                if ip == x.get_ip():
                    return

            tmp = Camera(ip=ip, tess=self.tess, cv_q=self.cv_q)
            self.cameras.add(tmp)
            p = Process(target=tmp.start, args=(self.tmp_queue, self.meta_queue))
            self.active.add((ip, p))
            p.start()
        except Exception as e:
            print(e)
            pass

    def cache(self, cv_tmp: Condition, cv_cache: Condition, cv_upload: Condition):
        """
        Extract numberplate from tmp directory and build confidence based off of tmp files.
        Once confidence is built, compare to existing cache data, remove duplications and upload (only if data is 2 min newer than cache)
        If cache does not contain such data, upload the file regardless of waiting time (2min).
        Save to cache.
        """
        try:
            with cv_tmp:
                temp_list = CachedNumberplateHandler.combine_tmp_data()
                if temp_list is not None:
                    refined_temp = CachedNumberplateHandler.improve_confidence(temp_list)
                    if refined_temp is not None:
                        in_cache, out_cache = CachedNumberplateHandler.compare_to_cached(refined_temp)
                        with cv_cache:
                            if len(in_cache) > 0:
                                CacheHandler.update_plate_cache(datetime.now().strftime(
                                    "%Y-%m-%d %H"), in_cache)
                            upload_list = in_cache + out_cache
                            with cv_upload:
                                if len(upload_list) > 0:
                                    upload_dict = CachedNumberplateHandler.compare_to_uploaded(upload_list)
                                    if upload_dict is not None:
                                        if len(upload_dict) > 0:
                                            upload_tuple = CachedNumberplateHandler.convert_dict_to_tuple(upload_dict)
                                            if len(upload_tuple) > 0:
                                                # Don't remove image from tuple - uploading everything with conf 0.6 >
                                                # upload_tuple = [x[:-1] for x in upload_tuple]
                                                uploaded = [x[:-1] for x in upload_tuple]
                                                CacheHandler.save_tmp("uploaded", datetime.now().strftime("%Y-%m-%d"),
                                                                      uploaded)
                                                self.upload_dataset(upload_tuple)
                                                print("Uploading: ", uploaded)

                                            self.cache_queue.put(upload_dict)
                                cv_upload.notify_all()
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
                    shallow_cameras = self.cameras.copy()
                    for x in shallow_cameras:
                        if x.get_ip() == process[0]:
                            self.cameras.discard(x)
                            break
            except Exception as e:
                print("Tried to remove process", e)

    def upload_dataset(self, data):
        try:
            url = "http://" + self.url + self.addplate
            if Request.post(self.interface, data, url) is False:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                CacheHandler.save_cache("offline", now, data)
        except Exception as e:
            print(e)
            pass

    def cleanup_temp(self, cv_tmp: Condition):
        with cv_tmp:
            try:
                pathlib.Path("../plateos-files/tmp/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("tmp")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        diff = now - datetime.strptime(x, "%Y-%m-%d %H:%M")
                        if timedelta(minutes=10) <= diff:
                            CacheHandler.remove("tmp", x)
            except Exception as e:
                print("Error on Cleaning tmp", e)
                pass
            cv_tmp.notify_all()

    # noinspection PyMethodMayBeStatic
    def cleanup_cache(self, cv_cache: Condition, cv_meta: Condition, cv_upload: Condition):
        with cv_cache:
            try:
                pathlib.Path("../plateos-files/cache/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("cache")
                if len(files) > 0:
                    for x in files:
                        file_last_date = datetime.strptime(x, "%Y-%m-%d %H")
                        now = datetime.now()
                        diff = now - file_last_date
                        if timedelta(days=90) <= diff:
                            CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
            except Exception as e:
                print("Error on Cleaning Cache", e)
                pass
            cv_cache.notify_all()

        with cv_meta:
            try:
                pathlib.Path("../plateos-files/meta/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("meta")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        file_last_date = datetime.strptime(x, "%Y-%m-%d %H:%M")
                        diff = now - file_last_date
                        if timedelta(days=20) <= diff:
                            CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
            except Exception as e:
                print("Error on Cleaning Meta", e)
                pass
            cv_meta.notify_all()

        with cv_upload:
            try:
                pathlib.Path("../plateos-files/uploaded/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("uploaded")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        diff = now - datetime.strptime(x, "%Y-%m-%d")
                        if timedelta(days=2) <= diff:
                            CacheHandler.remove("uploaded", x)
            except Exception as e:
                print("Error on Cleaning upload", e)
                pass
            cv_upload.notify_all()

    def offline_check(self):
        if Request.check_connectivity():
            try:
                pathlib.Path("../plateos-files/offline/").mkdir(parents=True, exist_ok=True)
                files = [f.replace('.npz', '') for f in listdir("../plateos-files/offline") if isfile(join("../plateos-files/offline", f))]
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
                data = []
                for x in self.cameras:
                    data.append(x.get_camera_data())
                # FrameHandler.get_all(self.camera_queue)
                # while not self.camera_queue.empty():
                #     obj = self.camera_queue.get_nowait()
                #     for cam in obj:
                #         data.append(cam.get_camera_data())
                Request.ping_location(self.interface, url, self.alias, data)
        except Exception as e:
            print(e)
            pass

    def tmp_queue_handler(self, cv: Condition):
        with cv:
            out = []
            while not self.tmp_queue.empty():
                val = self.tmp_queue.get_nowait()
                if val is not None:
                    out += val
            if len(out) > 0:
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                CacheHandler.save_tmp("tmp", now, out)
            cv.notify_all()

    def meta_queue_handler(self, cv: Condition, meta_time):
        while not meta_time.empty():
            prev_time = meta_time.get_nowait()
            now = datetime.now()
            if prev_time is not None:
                diff = now - prev_time
                with cv:
                    out = []
                    while not self.meta_queue.empty():
                        val = self.meta_queue.get_nowait()
                        if val is not None:
                            if diff > timedelta(minutes=3):
                                out += val

                    if len(out):
                        CacheHandler.save_meta("meta", now.strftime('%Y-%m-%d %H:%M'), out)
                    if diff > timedelta(minutes=3):
                        now = datetime.now()
                        meta_time.put(now)
                    else:
                        meta_time.put(prev_time)
                    cv.notify_all()
            else:
                now = datetime.now()
                meta_time.put(now)

    def cache_queue_handler(self, cv: Condition):
        with cv:
            out = []
            while not self.cache_queue.empty():
                val = self.cache_queue.get_nowait()
                if val is not None:
                    out += val
            if len(out) > 0:
                now = datetime.now().strftime('%Y-%m-%d %H')
                CacheHandler.save_cache("cache", now, out)
            cv.notify_all()
