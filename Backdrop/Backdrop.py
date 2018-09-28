import asyncio
import datetime
import sys
from os import listdir
from os.path import isfile, join
from threading import Thread

from Backdrop.BackdropHandler import BackdropHandler
from Caching.CacheHandler import CacheHandler
from Network.PortScanner import PortScanner
from Network.requestor import Request
from camera.Camera import Camera
from numberplate.Numberplate import Numberplate
from tess.tesseract import Tess


# noinspection PyBroadException
class Backdrop:

    def __init__(self, args, iprange, url):
        self.iprange = iprange
        self.camera = []
        self.tess = Tess(backdrop=self)
        self.active = set()
        self.scanner = PortScanner()
        self.username, self.password = args
        self.cached = []
        self.url = url
        self.last_upload = None
        self.backdrophandler = BackdropHandler(self, scanner=PortScanner(), iprange=iprange)

    async def scan(self):
        Thread(target=self.backdrophandler.start()).start()

    def add(self, a):
        try:
            tmp = Camera(username=self.username, password=self.password, ip=a, tess=self.tess, backdrop=self)
            p = Thread(target=tmp.start)
            self.active.add((a, p))
            p.start()
        except:
            pass

    def callback_tess(self, plate):
        print("Plate:", plate[0], "Province:", plate[1], "Confidence:", plate[2], "Date:", plate[3])
        self.cached.append(plate)

    def cache(self):
        try:
            if len(self.cached) >= 1:
                today = datetime.datetime.now().strftime('%Y-%m-%d %H')
                self.cached = Numberplate.improve(self.cached)
                if self.cached is not None:
                    res = CacheHandler.save("cache/", today, self.cached)
                    if res is not None:
                        self.upload_dataset(res)
                self.cached = []
        except Exception as e:
            print(e)
            pass

    def callback_camera(self, ip):
        print("Removing camera", ip)
        self.active.discard(ip)

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
            url = self.url+"db/addplate"
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


    def getActive(self):
        return self.active