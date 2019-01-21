from Backdrop.Backdrop import Backdrop
from Handlers.PropertyHandler import PropertyHandler

try:

    PropertyHandler.load_app()
    PropertyHandler.load_cv()
    PropertyHandler.load_numberplate()
    runner = Backdrop()
    runner.start()
except KeyboardInterrupt:
    print("Killing process...")
