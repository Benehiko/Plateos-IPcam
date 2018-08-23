import netifaces
import socket
import datetime
import requests

from Caching.CacheHandler import CacheHandler


class Request:

    @staticmethod
    def post(data, url):
        mac = netifaces.ifaddresses('eth0')[netifaces.AF_LINK]
        mac = mac[0].get('addr')
        out = []

        for x in data:
            plate, province, confidence, date = x
            d = [('plate', plate), ('province', province), ('confidence', confidence), ('time', date), ('mac', mac)]
            out.append(dict(d))

        if Request.check_connectivity():
            Request.send(url, out)
        else:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            CacheHandler.save("offline/", now, out)

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
            conn = socket.create_connection(('google.com', 443))
            conn.close()
            return True
        except Exception as e:
            print("Testing google ping", e)
            pass

        return False

