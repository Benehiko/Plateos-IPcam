from Backdrop.Backdrop import Backdrop
import asyncio

args = ("admin", ***REMOVED***)
url = "http://localhost:8080/Plateos/db/addplate"
runner = Backdrop(args=args, iprange="192.168.1.100-192.168.1.200", url=url)
loop = asyncio.get_event_loop()
loop.run_until_complete(runner.scan())
