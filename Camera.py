from Backdrop.Backdrop import Backdrop
from Network.PortScanner import PortScanner
import xml.etree.ElementTree as ET

import asyncio
import sys

#tree = ET.parse("settings.xml")
#root = tree.getroot()
#print(root)

try:
    scanner = PortScanner()
    active = scanner.scan("192.168.1.100-192.168.1.200")

    if len(active) > 0:
        args = ("admin", "Benehiko123!", active)
        runner = Backdrop(args)
        runner.run()
    else:
        print("Exiting...")
except KeyboardInterrupt:
    sys.exit(0)