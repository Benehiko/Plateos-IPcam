import io
import sys

import yaml

from Backdrop.Backdrop import Backdrop
import asyncio

stream = io.open("conf.yml", 'r', encoding='utf8')
configs = yaml.safe_load(stream)

# Camera Settings
camera = configs.get("camera")

# Device Settings
device = configs.get("device")

# Restful API Settings
restful = configs.get("restful")

runner = Backdrop(camera=camera, device=device, restful=restful)

loop = asyncio.get_event_loop()
runner.scan()
sys.exc_info()
