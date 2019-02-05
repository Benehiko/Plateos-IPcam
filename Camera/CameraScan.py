import socket
from threading import Thread


class CameraScan:

    # TODO: Add type mapping and return types to methods with correct descriptions

    def __init__(self):
        self.valid = set()

    def scan(self, iprange):
        self.valid = set()

        data = iprange.split("-")
        start = data[0]
        start = int(start[start.rfind(".") + 1:])

        end = data[1]
        end = int(end[end.rfind(".") + 1:])

        subip = iprange[:data[0].rfind(".") + 1]

        pool = set()
        for i in range(start, end + 1):
            ip = subip + str(i)
            pool.add(Thread(self.TCP_connect(ip, 1935, 0.5)))

        for p in pool:
            p.start()

        tmp = pool.copy()
        while len(pool) > 0:
            for process in tmp:
                try:
                    if process.is_alive() is False:
                        pool.discard(process)
                except Exception as e:
                    print("Camera Scan Error", e)
                    pass

        return self.valid

    def TCP_connect(self, ip, port_number, delay):
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        # noinspection PyBroadException
        try:
            TCPsock.connect((ip, port_number))
            self.valid.add(ip)
        except:
            pass

        return None
