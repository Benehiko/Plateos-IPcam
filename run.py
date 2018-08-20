from Backdrop.Backdrop import Backdrop
import asyncio
import xml.etree.ElementTree as ET

# tree = ET.parse("settings.xml")
# root = tree.getroot()
# print(root)
args = ("admin", ***REMOVED***)
runner = Backdrop(args=args, iprange="192.168.1.100-192.168.1.200")
loop = asyncio.get_event_loop()
loop.run_until_complete(runner.scan())