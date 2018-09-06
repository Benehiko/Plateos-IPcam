from Backdrop.Backdrop import Backdrop
import asyncio

args = ("admin", "jUa2kUzi")
url = "http://104.40.251.46:8080/Plateos/"
runner = Backdrop(args=args, iprange="192.168.1.2-192.168.1.200", url=url)
loop = asyncio.get_event_loop()
loop.run_until_complete(runner.scan())
