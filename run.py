import asyncio
import sys

from Backdrop.Backdrop import Backdrop
from DataHandler.PropertyHandler import PropertyHandler

PropertyHandler.load_app()
PropertyHandler.load_cv()
runner = Backdrop()

loop = asyncio.get_event_loop()
runner.scan()
sys.exc_info()
