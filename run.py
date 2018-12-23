import sys

from Backdrop.Backdrop import Backdrop
from DataHandler.PropertyHandler import PropertyHandler

PropertyHandler.load_app()
PropertyHandler.load_cv()
PropertyHandler.load_numberplate()
runner = Backdrop()
runner.scan()
sys.exc_info()
