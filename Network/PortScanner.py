import threading
import socket


class PortScanner(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

    def scan(self, iprange):
        print("Scanning for IP Camera's...")

        data = iprange.split("-")
        start = data[0]
        start = int(start[start.rfind(".")+1:])

        end = data[1]
        end = int(end[end.rfind(".")+1:])

        subip = iprange[:data[0].rfind(".")+1]

        output = {}
        threads = []
        active =[]

        for i in range(start, end+1):
            ip = subip+str(i)
            t = threading.Thread(target=self.TCP_connect, args=(ip, 1935, 3, output))
            threads.append(t)

        for x in range(0, len(threads)):
            threads[x].start()

        for t in range(0, len(threads)):
            threads[t].join()

        for i in range(start, end+1):
            if output[i]:
                active.append(subip+str(i))

        if len(active) > 0:
            print("Found: ", active)
        else:
            print("Could not find any IP Cameras")

        return active

    def TCP_connect(self, ip, port_number, delay, output):
        TCPsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        TCPsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        TCPsock.settimeout(delay)
        subip = int(ip[ip.rfind(".") + 1:])
        try:
            TCPsock.connect((ip, port_number))
            output[subip] = True
        except:
            output[subip] = False
