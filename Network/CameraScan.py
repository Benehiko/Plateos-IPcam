import socket
from threading import Thread


class CameraScan:

    def __init__(self):
        self.valid = []

    def scan(self, iprange):
        self.valid = []

        data = iprange.split("-")
        start = data[0]
        start = int(start[start.rfind(".") + 1:])

        end = data[1]
        end = int(end[end.rfind(".") + 1:])

        subip = iprange[:data[0].rfind(".") + 1]

        pool = []
        for i in range(start, end + 1):
            ip = subip + str(i)
            pool.append(Thread(self.TCP_connect(ip, 1935, 1)))

        for p in pool:
            p.start()

        for p in pool:
            p.join()

        return self.valid

    def TCP_connect(self, ip, port_number, delay):
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        # noinspection PyBroadException
        try:
            TCPsock.connect((ip, port_number))
            self.valid.append(ip)
        except:
            pass

        return None
