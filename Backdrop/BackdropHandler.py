import asyncio
import datetime
import pathlib
from multiprocessing import Process
from os import listdir
from os.path import isfile, join
from threading import Thread
from time import sleep

from Caching.CacheHandler import CacheHandler
from Network.requestor import Request
from camera.Camera import Camera
from numberplate.Numberplate import Numberplate
from tess.tesseract import Tess


class BackdropHandler:

    def __init__(self, backdrop, scanner, iprange, args, url):
        self.backdrop = backdrop
        self.scanner = scanner
        self.iprange = iprange
        self.username, self.password = args
        self.tess = Tess(backdrop=self)
        self.cached = []
        self.active = set()
        self.url = url


    def start(self):
        count = 0
        while True:
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)
            active = self.active
            print("Current Active cameras", active)
            tmp = self.scanner.scan(self.iprange, event_loop=event_loop)
            event_loop.close()
            active_ip = [x[0] for x in active]
            for x in tmp:
                if x not in active_ip:
                    self.add(x)
            sleep(60)
            self.check_alive()
            if count > 60:
                self.cleanup_cache()
                self.offline_check()
                count = 0
                self.ping_location()
            self.cache()
            count += 1

    def callback_tess(self, plate):
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2], "Date:", plate[3])
        self.cached.append(plate)

    def add(self, a):
        try:
            tmp = Camera(username=self.username, password=self.password, ip=a, tess=self.tess)
            p = Process(target=tmp.start)
            self.active.add((a, p))
            p.start()
        except Exception as e:
            print(e)
            pass

    def cache(self):
        cached = self.cached
        try:
            if len(cached) > 0:
                today = datetime.datetime.now().strftime('%Y-%m-%d %H')
                cached = Numberplate.improve(cached)
                if cached is not None:
                    if len(cached) > 0:
                        res = CacheHandler.save("cache/", today, cached)
                        if res is not None:
                            self.upload_dataset(res)
                self.cached = []
        except Exception as e:
            print(e)
            pass

    def check_alive(self):
        tmp = self.active.copy()
        for process in tmp:
            try:
                if process[1].is_alive() is False:
                    print("Process died")
                    self.active.discard(process)
            except Exception as e:
                print("Tried to remove process", e)

    def upload_dataset(self, data):
        try:
            url = self.url
            url = url+"db/addplate"
            Request.post(data, url)
        except:
            pass

    # noinspection PyMethodMayBeStatic
    def cleanup_cache(self):
        try:
            files = [f.replace('.npy.gz', '') for f in listdir("cache") if isfile(join("cache", f))]
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
                pathlib.Path("offline").mkdir(parents=False, exist_ok=True)
                files = [f.replace('.npy.gz', '') for f in listdir("offline") if isfile(join("offline", f))]
                if len(files) > 0:
                    for x in files:
                        tmp = CacheHandler.load("offline/", x).tolist()
                        Request.post(tmp, self.url)
                        CacheHandler.remove("offline/", x)
            except Exception as e:
                print(e)
                pass

    def ping_location(self):
        try:
            if Request.check_connectivity():
                url = self.url
                url = url+"db/addlocation"
                Request.ping_location(url)
        except:
            pass