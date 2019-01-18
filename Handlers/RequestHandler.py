import datetime
import netifaces
import subprocess
from base64 import b64encode
from io import BytesIO
from urllib.error import URLError

import requests
from PIL import Image

from Handlers.CacheHandler import CacheHandler


class Request:

    # TODO: Add type mapping and return types to methods with correct descriptions

    @staticmethod
    def post(interface, data, url):
        mac = Request.get_mac(interface)
        if mac is not None:
            out = []

            for x in data:
                plate, province, confidence, date, deviceMac, image = x
                if confidence < 0.6:
                    tmp = ""
                else:
                    image = Image.fromarray(image)
                    tmp = BytesIO()
                    image.save(tmp, "JPEG")
                    tmp.seek(0)
                    tmp = b64encode(tmp.read())

                d = [('plate', plate), ('province', province), ('confidence', confidence), ('time', date),
                     ('deviceMac', mac), ('cameraMac', deviceMac), ('image', tmp)]
                out.append(dict(d))

            # print("Posting:", out)
            if Request.check_connectivity():
                Request.send(url, out)
            else:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                CacheHandler.save_cache("offline", now, out)
        else:
            print("Mac is None")

    @staticmethod
    def send(url, data):
        try:
            r = requests.post(url, json=data)
            print(r.text)
            return True
        except Exception as e:
            print("Error\n", e)
            return False

    @staticmethod
    def check_connectivity():
        try:
            hostname = "8.8.8.8"
            response = subprocess.call(["ping", "-c", "3", hostname], stdout=subprocess.DEVNULL)
            if response == 0:
                return True
            else:
                return False
        except Exception as e:
            print("Connectivity Check: ", e)
            pass

        return False

    @staticmethod
    def ping_location(interface, url, alias, cameras):
        try:
            list_ip = netifaces.ifaddresses(interface)[netifaces.AF_INET]  # eth0
            ip = list_ip[len(list_ip) - 1]['addr']
            # device_ip = urlopen('http://ip.42.pl/raw').read()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            d = [('mac', Request.get_mac(interface)), ('ip', ip), ('time', now), ('alias', alias)]
            j = dict(d)
            t = dict([("device", j), ('cameras', cameras)])
            print("Posting:", t)
            Request.send(url, t)
        except URLError as e:
            print("Ping Location: ", e)
            pass

    @staticmethod
    def get_mac(interface):
        try:
            mac = netifaces.ifaddresses(interface)[netifaces.AF_LINK]  # eth0
            mac = mac[0].get('addr')
            return mac
        except Exception as e:
            print(e)
            pass
        return None

    @staticmethod
    def get(url, params):
        try:
            data = requests.get(url, params, timeout=3)
            return data.text
        except URLError as e:
            print(e)
            pass
        return None