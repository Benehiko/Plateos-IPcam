import asyncio
import concurrent
import pathlib
from asyncio import Condition
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from multiprocessing import Process
from os import listdir
from os.path import isfile, join
from threading import Thread
from time import sleep

import janus

from Camera.CameraScan import CameraScan
from Handlers.CacheHandler import CacheHandler
from Handlers.CachedNumberplateHandler import CachedNumberplateHandler
from Handlers.FrameHandler import FrameHandler
from Handlers.PropertyHandler import PropertyHandler
from Handlers.RequestHandler import Request
from Handlers.ThreadHandler import ThreadWithReturnValue
from Helper.ProcessHelper import ProcessHelper
from Views.Camera import Camera
from Views.Video import Video
from cvlib.ImageUtil import ImageUtil
from tess.tesseract import Tess


class BackdropHandler:

    # TODO: Add type mapping and return types to methods with correct descriptions
    # TODO: Resource handling of Temp (saving and restoring) isn't fast enough. Tmp loses out on saving data a lot.

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
        self.url = str(restful["url"]) + ":" + str(self.port)
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
        self.tmp_queue = None
        self.meta_queue = None
        self.cache_queue = None

        # Flags for File handling
        self.tmp_access = True
        self.meta_access = True
        self.cache_access = True

        # Condition for File handling
        self.c_tmp = Condition()
        self.c_meta = Condition()
        self.c_cache = Condition()
        self.c_upload = Condition()

        self.meta_time = None
        self.camera_queue = None
        self.cv_q = None
        self.frames_q = None

    def start(self, main_loop: asyncio.AbstractEventLoop, queue, cv_q, frames_q):
        self.tmp_queue = janus.Queue(loop=main_loop)
        self.meta_queue = janus.Queue(loop=main_loop)
        self.cache_queue = janus.Queue(loop=main_loop)
        self.meta_time = janus.Queue(loop=main_loop)

        self.camera_queue = queue
        self.cv_q = cv_q
        self.frames_q = frames_q

        event_loop = main_loop
        try:
            event_loop.run_in_executor(None, self.process_frames,
                                       self.tmp_queue.sync_q, self.meta_queue.sync_q, self.frames_q.sync_q,
                                       self.cv_q.sync_q, )
            event_loop.run_in_executor(None, self.scan_helper, self.frames_q)

            #asyncio.ensure_future(self.add_video(self.frames_q, self.cameras, self.active), loop=event_loop)
            asyncio.ensure_future(FrameHandler.clean(self.camera_queue.async_q), loop=event_loop)
            asyncio.ensure_future(self.location_update(), loop=event_loop)
            asyncio.ensure_future(self.cleanup_temp(), loop=event_loop)
            asyncio.ensure_future(self.cleanup_saved_files(), loop=event_loop)
            asyncio.ensure_future(self.offline_check(), loop=event_loop)
            asyncio.ensure_future(self.process_temp(self.cache_queue.async_q),
                                  loop=event_loop)
            asyncio.ensure_future(self.tmp_queue_handler(self.tmp_queue.async_q), loop=event_loop)
            asyncio.ensure_future(self.meta_queue_handler(self.meta_time.async_q, self.meta_queue.async_q),
                                  loop=event_loop)
            asyncio.ensure_future(self.cache_queue_handler(self.cache_queue.async_q), loop=event_loop)
            # asyncio.ensure_future(self.check_alive(), loop=event_loop)

            event_loop.run_forever()
        except Exception as e:
            print("Running Asyncio Tasks Error", e)
        finally:
            event_loop.run_until_complete(event_loop.shutdown_asyncgens())
            event_loop.close()

    def scan_helper(self, frames_q: janus.Queue):
        """
        Scan cameras on the network

        :return:
        """
        print("Starting to scan for cameras")
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
                    pool = []
                    loop = asyncio.new_event_loop()
                    try:
                        for x in non_active:
                            tmp = Camera(x)
                            self.cameras.add((x, tmp))
                            pool.append(asyncio.ensure_future(tmp.start(frames_q.async_q), loop=loop))
                            # p = Thread(target=tmp.start, args=(frames_q.sync_q,))
                            # self.active.add((x, coro))
                            # p.start()
                        loop.run_forever()
                    finally:
                        loop.run_until_complete(loop.shutdown_asyncgens())
                        loop.close()
            sleep(10)

    async def add_video(self, frames_q, cameras, active):
        videos = "demo.mp4"
        tmp = Video(videos)
        cameras.add((videos, tmp))
        p = Thread(target=tmp.start, args=(frames_q.sync_q,))
        active.add((videos, p))
        p.start()

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

    async def process_temp(self,
                           cache_q: janus.Queue.async_q):
        """
        Extract numberplate from tmp directory and build confidence based off of tmp files.
        Once confidence is built, compare to existing cache data, remove duplications and upload (only if data is 2 min newer than cache)
        If cache does not contain such data, upload the file regardless of waiting time (2min).
        Save to cache.
        :param cache_q:
        :param cv_upload: Condition
        :param cv_cache: Condition
        :type cv_tmp: Condition
        """
        while True:
            try:
                temp_list = await CachedNumberplateHandler.combine_tmp_data()
                if temp_list is not None and len(temp_list) > 0:
                    refined_temp = await CachedNumberplateHandler.improve_confidence(temp_list)
                    upload_list = []
                    if refined_temp is not None:
                        in_cache, out_cache = await CachedNumberplateHandler.compare_to_cached(refined_temp)
                        if len(in_cache) > 0:
                            await CacheHandler.update_plate_cache(datetime.now().strftime(
                                "%Y-%m-%d %H"), in_cache)
                        upload_list = in_cache + out_cache

                    if len(upload_list) > 0:
                        upload_dict = await CachedNumberplateHandler.compare_to_uploaded(upload_list)
                        if upload_dict is not None:
                            if len(upload_dict) > 0:
                                with_images = await CachedNumberplateHandler.get_tmp_images(upload_dict)
                                upload_tuple = CachedNumberplateHandler.convert_dict_to_tuple(
                                    with_images)
                                if len(upload_tuple) > 0:
                                    # Don't remove image from tuple - uploading everything with conf 0.6 >
                                    # upload_tuple = [x[:-1] for x in upload_tuple]
                                    uploaded = [x[:-1] for x in upload_tuple]
                                    await CacheHandler.save_upload("uploaded",
                                                                   datetime.now().strftime("%Y-%m-%d"),
                                                                   uploaded)
                                    await self.upload_dataset(upload_tuple)
                                    print("Uploading: ", uploaded)

                                    cache_q.put_nowait(upload_dict)

            except Exception as e:
                print(e)
                pass
            await asyncio.sleep(1)

    async def check_alive(self):
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
            await asyncio.sleep(5)

    async def upload_dataset(self, data):
        """
        Upload finalised data
        :param data:
        :return:
        """
        try:
            url = "http://" + self.url + self.addplate
            if Request.check_connectivity(url.split(":")[1].replace("/", "")):
                if Request.post(self.interface, data, url) is False:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    await CacheHandler.save_cache("offline", now, data)
        except Exception as e:
            print(e)
            pass

    async def cleanup_temp(self):
        """
        Cleanup temporary directory at the temp-keep property rate.

        :param cv_tmp:
        :return:
        """
        while True:
            try:
                files = CacheHandler.get_file_list("tmp")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        diff = now - datetime.strptime(x, "%Y-%m-%d %H:%M")
                        if timedelta(seconds=int(self.rates["temp-keep"])) <= diff:
                            print("Cleaning up temp...[rate=", self.rates["temp-keep"], "]")
                            CacheHandler.remove("tmp", x)
                            CacheHandler.remove("tmp/images", x)
            except Exception as e:
                print("Error on Cleaning tmp", e)
                pass
            await asyncio.sleep(10)

    # noinspection PyMethodMayBeStatic
    async def cleanup_saved_files(self):
        """
        Cleanup saved files in all sectors (cache, meta, uploaded) at the cache-keep, meta-keep and uploaded-keep rates

        :param cv_cache:
        :param cv_meta:
        :param cv_upload:
        :return:
        """
        while True:
            try:
                # pathlib.Path("../plateos-files/cache/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("cache")
                if len(files) > 0:
                    for x in files:
                        file_last_date = datetime.strptime(x, "%Y-%m-%d %H")
                        now = datetime.now()
                        diff = now - file_last_date
                        if timedelta(seconds=int(self.rates["cache-keep"])) <= diff:
                            print("Cleaning up cache...[rate=", self.rates["cache-keep"], "]")
                            CacheHandler.remove("cache", file_last_date.strftime("%Y-%m-%d %H"))
                            CacheHandler.remove("cache/images", file_last_date.strftime("%Y-%m-%d %H"))
            except Exception as e:
                print("Error on Cleaning Cache", e)
                pass
                # cv_cache.notify_all()
            try:
                # pathlib.Path("../plateos-files/meta/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("meta")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        file_last_date = datetime.strptime(x, "%Y-%m-%d %H:%M")
                        diff = now - file_last_date
                        if timedelta(seconds=int(self.rates["meta-keep"])) <= diff:
                            print("Cleaning up meta...[rate=", self.rates["meta-keep"], "]")
                            CacheHandler.remove("meta", file_last_date.strftime("%Y-%m-%d %H:%M"))
            except Exception as e:
                print("Error on Cleaning Meta", e)
                pass
                # cv_meta.notify_all()

            try:
                # pathlib.Path("../plateos-files/uploaded/").mkdir(parents=True, exist_ok=True)
                files = CacheHandler.get_file_list("uploaded")
                if len(files) > 0:
                    now = datetime.now()
                    for x in files:
                        diff = now - datetime.strptime(x, "%Y-%m-%d")
                        if timedelta(seconds=int(self.rates["uploaded-keep"])) <= diff:
                            print("Cleaning up uploaded...[rate=", self.rates["uploaded-keep"], "]")
                            CacheHandler.remove("uploaded", x)
            except Exception as e:
                print("Error on Cleaning upload", e)
                pass
            await asyncio.sleep(10)

    async def offline_check(self):
        """
        Check offline data (saved data when network is offline) for upload.
        :return:
        """
        while True:
            if Request.check_connectivity(self.url.split(":")[0]):
                try:
                    pathlib.Path("../plateos-files/offline/").mkdir(parents=True, exist_ok=True)
                    files = [f.replace('.npz', '') for f in listdir("../plateos-files/offline") if
                             isfile(join("../plateos-files/offline", f))]
                    if len(files) > 0:
                        for x in files:
                            tmp = await CacheHandler.load("offline", x)
                            if tmp is not None:
                                if Request.post(self.interface, tmp.tolist(), self.url):
                                    print("Offline uploaded...")
                                    CacheHandler.remove("offline", x)
                except Exception as e:
                    print("Offline upload Error", e)
                    pass
            await asyncio.sleep(10)

    async def location_update(self):
        """
        Give updates to the server about the device (online status)
        :return:
        """
        t = datetime.now()
        while True:
            if timedelta(seconds=int(self.rates["location-update"])) < (datetime.now() - t):
                print("Updating location...[rate=", self.rates["location-update"], "]")
                try:
                    url = "http://" + self.url + self.addlocation
                    if Request.check_connectivity(url.split(":")[1].replace("/", "")):
                        data = []
                        for x in self.cameras:
                            data.append(x[1].get_camera_data())
                        Request.ping_location(self.interface, url, self.alias, data)
                except Exception as e:
                    print("Ping Location Error", e)
                    pass
                t = datetime.now()
            await asyncio.sleep(10)

    async def tmp_queue_handler(self, tmp_queue: janus.Queue.async_q):
        """
        Temp data across threads/processes - save temp files (used to build confidence)
        :param tmp_queue:
        :param cv:
        :return:
        """
        while True:
            try:
                out = []
                while not tmp_queue.empty():
                    val = await tmp_queue.get()
                    if val is not None:
                        out += val
                    tmp_queue.task_done()

                if len(out) > 0:
                    print("Saving Temp...")
                    now = datetime.now().strftime('%Y-%m-%d %H:%M')
                    await CacheHandler.save_tmp("tmp", now, out)
            except Exception as e:
                pass
            await asyncio.sleep(1)

    async def meta_queue_handler(self, meta_time: janus.Queue.async_q, meta_queue: janus.Queue.async_q):
        """
        Handle meta data across threads/processes - save meta data according to meta-rate property
        :param meta_queue:
        :param cv:
        :param meta_time:
        :return:
        """
        t = datetime.now()
        while True:
            try:
                now = datetime.now()
                diff = now - t
                out = []
                while not meta_queue.empty():
                    val = await meta_queue.get()

                    if val is not None:
                        out += val
                    meta_queue.task_done()

                if len(out):
                    if diff > timedelta(seconds=int(self.rates["meta-rate"])):
                        print("Saving Meta...[rate=", self.rates["meta-rate"], "]")
                        await CacheHandler.save_meta("meta", now.strftime('%Y-%m-%d %H:%M'), out)
                        t = datetime.now()
            except Exception as e:
                pass

            await asyncio.sleep(1)

    async def cache_queue_handler(self, cache_q: janus.Queue.async_q):
        """
        Handle cache data across threads/processes - save cache data
        :param cache_q:
        :param cv:
        :return:
        """
        while True:
            out = []
            while not cache_q.empty():
                val = cache_q.get_nowait()
                if val is not None:
                    out += val
                cache_q.task_done()
            if len(out) > 0:
                print("Saving Cache...")
                now = datetime.now().strftime('%Y-%m-%d %H')
                await CacheHandler.save_cache("cache", now, out)
            await asyncio.sleep(1)

    def process_frames(self, tmp_q: janus.Queue.sync_q, meta_q: janus.Queue.sync_q, frames_q: janus.Queue.sync_q,
                       cv_q: janus.Queue.sync_q):
        process = ProcessHelper(cv_q)
        print("Starting processing frames")
        while True:
            camera_data = []
            processed = []
            results = []
            meta = []
            while not frames_q.empty():
                val = frames_q.get_nowait()
                if val is not None:
                    camera_data.append(val)
                frames_q.task_done()

            # Val contains {"mac": mac, "ip": ip, "image": img}
            # Camera_data is list of Val
            if len(camera_data) > 0:
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

                tmp_q.put_nowait(results)
                meta_q.put_nowait(meta)
                # tmp_q.join()
                # meta_q.join()
                # sleep(1)
