import base64
import datetime
import netifaces
import subprocess
from base64 import b64encode
from io import BytesIO
from urllib.error import URLError

import requests
from PIL import Image


class Request:

    # TODO: Add type mapping and return types to methods with correct descriptions

    @staticmethod
    def post(interface, data, url):
        mac = Request.get_mac(interface)
        if mac is not None:
            out = []

            for x in data:
                plate, province, confidence, date, deviceMac, image = x
                if confidence < 0.4:
                    tmp = ""
                else:
                    image = Image.fromarray(image)
                    tmp = BytesIO()
                    image.save(tmp, "JPEG")
                    tmp.seek(0)
                    tmp = base64.standard_b64encode(tmp.read()).decode('utf-8')

                d = [('plate', plate), ('province', province), ('confidence', confidence), ('time', date),
                     ('deviceMac', mac), ('cameraMac', deviceMac), ('image', tmp)]
                out.append(dict(d))

            # print("Posting:", out)
            return Request.send(url, out)
        else:
            print("Mac is None")
        return False

    @staticmethod
    def send(url, data):
        try:
            r = requests.post(url, json=data, timeout=3)
            if r.status_code == 200:
                return True
        except Exception as e:
            print("Couldn't Post")
            pass
        return False

    @staticmethod
    def check_connectivity(hostname="8.8.8.8"):
        try:
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
    def custom_check_connectivity(url):
        try:
            hostname = url
            response = subprocess.call(["ping", "-c", "3", hostname], stdout=subprocess.DEVNULL)
            if response == 0:
                return True

        except Exception as e:
            print("Custom Connectivity Check", e)
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
            # print("Posting:", t)
            Request.send(url, t)
        except URLError as e:
            # print("Ping Location: ", e)
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
