import sys

from Backdrop.Backdrop import Backdrop
from Handlers.PropertyHandler import PropertyHandler

PropertyHandler.load_app()
PropertyHandler.load_cv()
PropertyHandler.load_numberplate()
runner = Backdrop()
runner.start()
sys.exc_info()
