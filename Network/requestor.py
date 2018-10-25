import datetime
import netifaces
from urllib.error import URLError
from urllib.request import urlopen

import requests

from Caching.CacheHandler import CacheHandler


class Request:

    @staticmethod
    def post(data, url):
        mac = Request.get_mac()
        if mac is not None:
            out = []

            for x in data:
                plate, province, confidence, date = x
                d = [('plate', plate), ('province', province), ('confidence', confidence), ('time', date), ('mac', mac)]
                out.append(dict(d))

            print("Posting:", out)
            if Request.check_connectivity():
                Request.send(url, out)
            else:
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                CacheHandler.save("offline/", now, out)
        else:
            print("Mac is None")

    @staticmethod
    def send(url, data):
        try:
            r = requests.post(url, json=data)
            print(r.text)
            return True
        except Exception as e:
            print("Error\n",e)
            return False

    @staticmethod
    def check_connectivity():
        try:
            request = urlopen('http://google.com', timeout=3)
            if request.status == 200:
                return True
            else:
                return False
        except Exception as e:
            print("Connectivity Check: ", e)
            pass

        return False

    @staticmethod
    def ping_location(url):
        try:
            list_ip = netifaces.ifaddresses('eth0')[netifaces.AF_INET]
            ip = list_ip[len(list_ip) - 1]['addr']
            #device_ip = urlopen('http://ip.42.pl/raw').read()
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            d = [('mac', Request.get_mac()), ('ip', ip), ('timestamp', now)]
            j = dict(d)
            print("Posting:", j)
            Request.send(url, j)
        except URLError as e:
            print("Ping Location: ", e)
            pass

    @staticmethod
    def get_mac():
        try:
            mac = netifaces.ifaddresses('eth0')[netifaces.AF_LINK]
            mac = mac[0].get('addr')
            return mac
        except Exception as e:
            print(e)
            pass
        return None

