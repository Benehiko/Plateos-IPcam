import concurrent
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import pathlib
from multiprocessing import Process, Queue, Condition
from os import listdir
from os.path import isfile, join
from threading import Thread
from time import sleep

from Handlers.FrameHandler import FrameHandler
from Helper.ProcessHelper import ProcessHelper
from Views.Camera import Camera
from Camera.CameraScan import CameraScan
from Handlers.CacheHandler import CacheHandler
from Handlers.CachedNumberplateHandler import CachedNumberplateHandler
from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from Handlers.ThreadHandler import ThreadWithReturnValue
from cvlib.ImageUtil import ImageUtil
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

        # Rates Settings
        self.rates = PropertyHandler.app_settings["rates"]

        # Processing Settings
        self.processing = PropertyHandler.app_settings["processing"]

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
        self.frames_q = None

    def start(self, queue, cv_q, frames_q):
        self.camera_queue = queue
        self.cv_q = cv_q
        self.frames_q = frames_q

        scan_helper = Thread(target=self.scan_helper)
        scan_helper.start()

        process_frames = Process(target=self.process_frames, args=(self.tmp_queue, self.meta_queue, self.frames_q))
        process_frames.start()

        clean_frame = Thread(target=FrameHandler.clean)
        clean_frame.start()

        ping_location = Thread(target=self.location_update)
        ping_location.start()

        cleanup_temp = Thread(target=self.cleanup_temp, args=(self.c_tmp,))
        cleanup_temp.start()

        cleanup_cache = Thread(target=self.cleanup_saved_files,
                               args=(self.c_cache, self.c_meta, self.c_upload,))
        cleanup_cache.start()

        offline_check = Thread(target=self.offline_check)
        offline_check.start()

        tmp_queue_handler = Thread(target=self.tmp_queue_handler, args=(self.c_tmp,))
        tmp_queue_handler.start()

        meta_queue_handler = Thread(target=self.meta_queue_handler, args=(self.c_meta, self.meta_time))
        meta_queue_handler.start()

        cache_queue_handler = Thread(target=self.cache_queue_handler, args=(self.c_cache,))
        cache_queue_handler.start()

        cache = Thread(target=self.process_temp, args=(self.c_tmp, self.c_cache, self.c_upload,))
        cache.start()

        check_alive = Thread(target=self.check_alive)
        check_alive.start()

        clean_frame.join()
        ping_location.join()
        cleanup_temp.join()
        cleanup_cache.join()
        offline_check.join()
        tmp_queue_handler.join()
        meta_queue_handler.join()
        cache_queue_handler.join()
        cache.join()
        check_alive.join()
        scan_helper.join()
        process_frames.join()

    def scan_helper(self):
        """
        Scan cameras on the network

        :return:
        """
        while True:
            t_camera = ThreadWithReturnValue(target=self.scanner.scan,
                                             args=(PropertyHandler.app_settings["camera"]["iprange"],))
            t_camera.start()
            found_camera = t_camera.join()
            non_active = set()
            if len(found_camera) > 0:
                tmp_cameras = [x[0] for x in self.cameras]
                for x in found_camera:
                    if x not in tmp_cameras:
                        non_active.add(x)

                if len(non_active) > 0:
                    for x in non_active:
                        tmp = Camera(ip=x)
                        self.cameras.add((x, tmp))
                        p = Process(target=tmp.start, args=(self.frames_q,))
                        self.active.add((x, p))
                        p.start()
            sleep(10)

    def add(self, ip, cameras, active):
        """
        Add Camera to camera list

        :param active:
        :param cameras:
        :param ip:
        :return:
        """
        try:

            for x in self.cameras:
                if ip == x[0]:
                    return False

            tmp = Camera(ip=ip)
            self.cameras.add((ip, tmp))
            p = Process(target=tmp.start, args=(self.frames_q,))
            self.active.add((ip, p))
            p.start()
        except Exception as e:
            print(e)
            pass

    def process_temp(self, cv_tmp: Condition, cv_cache: Condition, cv_upload: Condition):
        """
        Extract numberplate from tmp directory and build confidence based off of tmp files.
        Once confidence is built, compare to existing cache data, remove duplications and upload (only if data is 2 min newer than cache)
        If cache does not contain such data, upload the file regardless of waiting time (2min).
        Save to cache.
        :param cv_upload: Condition
        :param cv_cache: Condition
        :type cv_tmp: Condition
        """
        while True:
            try:
                with cv_tmp:
                    temp_list = CachedNumberplateHandler.combine_tmp_data()
                    if temp_list is not None:
                        print("Building Confidence...")
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
                                                upload_tuple = CachedNumberplateHandler.convert_dict_to_tuple(
                                                    upload_dict)
                                                if len(upload_tuple) > 0:
                                                    # Don't remove image from tuple - uploading everything with conf 0.6 >
                                                    # upload_tuple = [x[:-1] for x in upload_tuple]
                                                    uploaded = [x[:-1] for x in upload_tuple]
                                                    CacheHandler.save_tmp("uploaded",
                                                                          datetime.now().strftime("%Y-%m-%d"),
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
            sleep(10)

    def check_alive(self):
        """
        Check if a camera is alive or not. Remove it from the camera list.
        :return:
        """
        while True:
            tmp = self.active.copy()
            for process in tmp:
                try:
                    if process[1].is_alive() is False:
                        self.active.discard(process)
                        shallow_cameras = self.cameras.copy()
                        for x in shallow_cameras:
                            if x[0] == process[0]:
                                self.cameras.discard(x)
                                break
                except Exception as e:
                    print("Tried to remove process", e)
            sleep(5)

    def upload_dataset(self, data):
        """
        Upload finalised data
        :param data:
        :return:
        """
        try:
            url = "http://" + self.url + self.addplate
            if Request.post(self.interface, data, url) is False:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                CacheHandler.save_cache("offline", now, data)
        except Exception as e:
            print(e)
            pass

    def cleanup_temp(self, cv_tmp: Condition):
        """
        Cleanup temporary directory at the temp-keep property rate.

        :param cv_tmp:
        :return:
        """
        t = datetime.now()
        while True:
            if timedelta(minutes=1) < (datetime.now() - t):
                print("Cleaning up temp...")
                with cv_tmp:
                    try:
                        # pathlib.Path("../plateos-files/tmp/").mkdir(parents=True, exist_ok=True)
                        files = CacheHandler.get_file_list("tmp")
                        if len(files) > 0:
                            now = datetime.now()
                            for x in files:
                                diff = now - datetime.strptime(x, "%Y-%m-%d %H:%M")
                                if timedelta(seconds=int(self.rates["temp-keep"])) <= diff:
                                    CacheHandler.remove("tmp", x)
                    except Exception as e:
                        print("Error on Cleaning tmp", e)
                        pass
                    cv_tmp.notify_all()
                t = datetime.now()

    # noinspection PyMethodMayBeStatic
    def cleanup_saved_files(self, cv_cache: Condition, cv_meta: Condition, cv_upload: Condition):
        """
        Cleanup saved files in all sectors (cache, meta, uploaded) at the cache-keep, meta-keep and uploaded-keep rates

        :param cv_cache:
        :param cv_meta:
        :param cv_upload:
        :return:
        """
        t = datetime.now()
        while True:
            if timedelta(minutes=1) < (datetime.now() - t):
                print("Cleaning up cache...")
                with cv_cache:
                    try:
                        # pathlib.Path("../plateos-files/cache/").mkdir(parents=True, exist_ok=True)
                        files = CacheHandler.get_file_list("cache")
                        if len(files) > 0:
                            for x in files:
                                file_last_date = datetime.strptime(x, "%Y-%m-%d %H")
                                now = datetime.now()
                                diff = now - file_last_date
                                if timedelta(seconds=int(self.rates["cache-keep"])) <= diff:
                                    CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
                    except Exception as e:
                        print("Error on Cleaning Cache", e)
                        pass
                    cv_cache.notify_all()

                with cv_meta:
                    try:
                        # pathlib.Path("../plateos-files/meta/").mkdir(parents=True, exist_ok=True)
                        files = CacheHandler.get_file_list("meta")
                        if len(files) > 0:
                            now = datetime.now()
                            for x in files:
                                file_last_date = datetime.strptime(x, "%Y-%m-%d %H:%M")
                                diff = now - file_last_date
                                if timedelta(seconds=int(self.rates["meta-keep"])) <= diff:
                                    CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
                    except Exception as e:
                        print("Error on Cleaning Meta", e)
                        pass
                    cv_meta.notify_all()

                with cv_upload:
                    try:
                        # pathlib.Path("../plateos-files/uploaded/").mkdir(parents=True, exist_ok=True)
                        files = CacheHandler.get_file_list("uploaded")
                        if len(files) > 0:
                            now = datetime.now()
                            for x in files:
                                diff = now - datetime.strptime(x, "%Y-%m-%d")
                                if timedelta(seconds=int(self.rates["uploaded-keep"])) <= diff:
                                    CacheHandler.remove("uploaded", x)
                    except Exception as e:
                        print("Error on Cleaning upload", e)
                        pass
                    cv_upload.notify_all()
                t = datetime.now()

    def offline_check(self):
        """
        Check offline data (saved data when network is offline) for upload.
        :return:
        """
        t = datetime.now()
        while True:
            if timedelta(minutes=1) < (datetime.now() - t):
                print("Checking offline cache...")
                if Request.check_connectivity():
                    try:
                        pathlib.Path("../plateos-files/offline/").mkdir(parents=True, exist_ok=True)
                        files = [f.replace('.npz', '') for f in listdir("../plateos-files/offline") if
                                 isfile(join("../plateos-files/offline", f))]
                        if len(files) > 0:
                            for x in files:
                                tmp = CacheHandler.load("offline", x).tolist()
                                if tmp is not None:
                                    upload_tuple = CachedNumberplateHandler.convert_dict_to_tuple(tmp)
                                    if Request.post(self.interface, upload_tuple, self.url):
                                        CacheHandler.remove("offline", x)
                    except Exception as e:
                        print("Offline Check", e)
                        pass
                t = datetime.now()

    def location_update(self):
        """
        Give updates to the server about the device (online status)
        :return:
        """
        t = datetime.now()
        while True:
            if timedelta(seconds=int(self.rates["location-update"])) < (datetime.now() - t):
                try:
                    if Request.check_connectivity():
                        url = "http://" + self.url + self.addlocation
                        data = []
                        for x in self.cameras:
                            data.append(x[1].get_camera_data())
                        Request.ping_location(self.interface, url, self.alias, data)
                except Exception as e:
                    print("Ping Location Error", e)
                    pass
                t = datetime.now()

    def tmp_queue_handler(self, cv: Condition):
        """
        Temp data across threads/processes - save temp files (used to build confidence)
        :param cv:
        :return:
        """
        while True:
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
            sleep(0.2)

    def meta_queue_handler(self, cv: Condition, meta_time):
        """
        Handle meta data across threads/processes - save meta data according to meta-rate property
        :param cv:
        :param meta_time:
        :return:
        """
        while True:
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
                                if diff > timedelta(seconds=int(self.rates["meta-rate"])):
                                    out += val

                        if len(out):
                            CacheHandler.save_meta("meta", now.strftime('%Y-%m-%d %H:%M'), out)
                        if diff > timedelta(seconds=int(self.rates["meta-rate"])):
                            now = datetime.now()
                            meta_time.put(now)
                        else:
                            meta_time.put(prev_time)
                        cv.notify_all()
                else:
                    now = datetime.now()
                    meta_time.put(now)
            sleep(0.2)

    def cache_queue_handler(self, cv: Condition):
        """
        Handle cache data across threads/processes - save cache data
        :param cv:
        :return:
        """
        while True:
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
            sleep(0.2)

    def process_frames(self, tmp_q, meta_q, frames_q):
        process = ProcessHelper(self.cv_q)

        while True:
            camera_data = []
            processed = []
            results = []
            meta = []
            while not frames_q.empty():
                val = frames_q.get_nowait()
                if val is not None:
                    camera_data.append(val)
            # Val contains {"mac": mac, "ip": ip, "image": img}
            # Camera_data is list of Val
            if len(camera_data) > 0:
                print("Processing Batched Frames...")
                with ThreadPoolExecutor(max_workers=int(self.processing["max-workers"])) as executor:
                    futures = {executor.submit(process.analyse_frames, data["image"]): data for data in camera_data}
                    for future in concurrent.futures.as_completed(futures):
                        tmp = futures[future]
                        ip = tmp["ip"]
                        mac = tmp["mac"]
                        og_img = tmp["image"]
                        try:
                            data = future.result()
                            result, drawn, raw, __ = data
                            if result is not None:
                                if len(result) > 0:
                                    t = ThreadWithReturnValue(target=self.tess.multi, args=(result,))
                                    t.start()
                                    tmp = t.join()
                                    r = [x for x in tmp if len(x) > 3]
                                    if len(r) > 0:
                                        results.append({"camera": mac, "results": r})

                                    allowed = [x for x in tmp if 3 <= x["char-len"] <= 8]
                                    if len(allowed) > 0:
                                        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        t_image = ImageUtil.compress(og_img, max_w=1080, quality=60)
                                        meta.append(
                                            {"camera": mac, "time": time, "original": t_image, "results": allowed})

                            if drawn is not None:
                                image = drawn
                            else:
                                image = og_img

                            FrameHandler.add_obj([ip, image])
                        except Exception as e:
                            print("ThreadPool ProcessHelper exception: ", e)
                        else:
                            processed.append(data)

                tmp_q.put(results)
                meta_q.put(meta)
