import sys

from Backdrop.Backdrop import Backdrop
import asyncio

args = ("admin", ***REMOVED***)
url = "http://104.40.251.46:8080/Plateos/"
runner = Backdrop(args=args, iprange="192.168.1.110-192.168.1.114", url=url)
loop = asyncio.get_event_loop()
runner.scan()
sys.exc_info()