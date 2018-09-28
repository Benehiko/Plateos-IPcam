import asyncio
import socket


# noinspection PyMethodMayBeStatic
class PortScanner:

    def scan(self, iprange, event_loop):
        print("Scanning for IP Camera's...")

        data = iprange.split("-")
        start = data[0]
        start = int(start[start.rfind(".") + 1:])

        end = data[1]
        end = int(end[end.rfind(".") + 1:])

        subip = iprange[:data[0].rfind(".") + 1]

        pool = []
        for i in range(start, end + 1):
            ip = subip + str(i)
            pool.append(asyncio.ensure_future(self.TCP_connect(ip, 1935, 3), loop=event_loop))

        active = event_loop.run_until_complete(asyncio.gather(*pool))
        active = [x for x in active if x is not None]

        if len(active) > 0:
            print("Found: ", active)
        else:
            print("Could not find any IP Cameras")

        return active

    async def TCP_connect(self, ip, port_number, delay):
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        subip = int(ip[ip.rfind(".") + 1:])
        # noinspection PyBroadException
        try:
            TCPsock.connect((ip, port_number))
            return ip
        except:
            pass

        return None
