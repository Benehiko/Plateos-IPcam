import asyncio
import datetime
import pathlib
from multiprocessing import Process
from os import listdir
from os.path import isfile, join

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
        self.old_time = datetime.datetime.now()


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
                # Add multiple camera's
                if x not in active_ip:
                    self.add(x)
                    self.add(x)
                    self.add(x)
                    self.add(x)

            # Use timedelta maybe ? ?
            now = datetime.datetime.now()
            diff = now - self.old_time
            if datetime.timedelta(minutes=1) < diff:
            # sleep(60)
                self.check_alive()
                if datetime.timedelta(minutes=60) < diff:
            # if count > 60:
                    self.cleanup_cache()
                    self.offline_check()
                # count = 0
                    self.ping_location()
            # count += 1

    def callback_tess(self, plate):
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2], "Date:", plate[3])
        self.cached.append(plate)
        return

    def add(self, a):
        try:
            tmp = Camera(username=self.username, password=self.password, ip=a, tess=self.tess)
            p = Process(target=tmp.start)
            self.active.add((a, p))
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
                    res = CacheHandler.save("cache/", today, c)
                    if res is not None:
                        print("Would have uploaded: ", res)
                        # BackdropHandler.upload_dataset(res)
                        # self.cached = []
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

    @staticmethod
    def upload_dataset(data):
        try:
            url = "http://104.40.251.46:8080/Plateos/db/addplate"
            Request.post(data, url)
        except Exception as e:
            print(e)
            pass

    # noinspection PyMethodMayBeStatic
    def cleanup_cache(self):
        try:
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
                url = self.url+"db/addlocation"
                Request.ping_location(url)
        except:
            pass