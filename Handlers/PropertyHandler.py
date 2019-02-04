import io
from multiprocessing import Queue

import yaml


class PropertyHandler:
    # TODO: Add type mapping and return types to methods with correct descriptions
    cv_queue = Queue()
    numberplate = {}
    app_settings = {
        "camera": {
            "username": "",
            "password": "",
            "iprange": "",
            "restful": {
                "base": "",
                "snap": {
                    "cmd": "",
                    "channel": 0,
                },
                "mac": {
                    "cmd": ""
                },
                "info": {
                    "cmd": ""
                }
            }
        },
        "restful": {
            "url": "",
            "port": "",
            "addplate": "",
            "addlocation": ""
        },
        "device": {
            "alias": "",
            "interface": ""
        },
        "rates": {
            "location-update": 60,
            "temp-keep": 480,
            "meta-keep": 1728000,
            "cache-keep": 7776000,
            "uploaded-keep": 172800,
            "meta-rate": 180
        },
        "processing": {
            "max-workers": 4
        }

    }

    cv_settings = {
        "shape": {
            "area": {"min": 0.1, "max": 100},
            "height": {"min": 0.1, "max": 100},
            "width": {"min": 0.1, "max": 100},
            "angle": {"min": 0, "max": 180}
        },
        "char": {
            "area": {"min": 0.1, "max": 100},
            "height": {"min": 0.1, "max": 100},
            "width": {"min": 0.1, "max": 100},
            "morph": {"min": 1, "max": 9}
        },
        "preprocessing": {
            "morph": {"height": 8, "width": 20},
            "mask": {"lower": 0, "upper": 255},
            "otsu": 0,
            "erode": {"min": 0, "max": 255}
        }
    }

    def __init__(self):
        self.cv_settings = PropertyHandler.load_cv()
        PropertyHandler.cv_settings = self.cv_settings
        self.cv_queue.put(self.cv_settings)

    @staticmethod
    def load_app():
        try:
            configs = PropertyHandler.load("conf")
            # Camera Settings
            camera = configs.get("camera")

            # Device Settings
            device = configs.get("device")

            # Restful API Settings
            restful = configs.get("restful")

            # Rates Settings
            rates = configs.get("rates")

            # Processing Settings
            processing = configs.get("processing")

            PropertyHandler.app_settings = {
                "camera": camera,
                "device": device,
                "restful": restful,
                "rates": rates,
                "processing": processing
            }
        except Exception as e:
            print(e)
            PropertyHandler.save("conf.yml", PropertyHandler.app_settings)

    @staticmethod
    def load_cv():
        try:
            configs = PropertyHandler.load("detection")
            # Character detection
            char = configs.get("char")

            # Preprocessing (before shape detection)
            preprocessing = configs.get("preprocessing")

            # Shape detection
            shape = configs.get("shape")

            cv_settings = {
                "shape": shape,
                "char": char,
                "preprocessing": preprocessing
            }
            PropertyHandler.cv_settings = cv_settings
            return cv_settings

        except Exception as e:
            print(e)
            PropertyHandler.save("detection.yml", PropertyHandler.cv_settings)

    @staticmethod
    def load_numberplate():
        try:
            data = PropertyHandler.load("numberplate")
            PropertyHandler.numberplate = data
        except Exception as e:
            print(e)

    @staticmethod
    def load(file):
        try:
            stream = io.open(file + ".yml", 'r', encoding='utf8')
            data = yaml.safe_load(stream)
            return data
        except Exception as e:
            print(e)

    @staticmethod
    def save(filename, data):
        stream = io.open(filename, 'w', encoding='utf8')
        yaml.dump(data, stream, default_flow_style=False)

    @staticmethod
    def set_cv_settings(settings):
        while not PropertyHandler.cv_queue.empty():
            PropertyHandler.cv_queue.get()
        PropertyHandler.cv_queue.put(settings)
        PropertyHandler.cv_settings = settings

    @staticmethod
    def get_cv_settings(queue):
        while not PropertyHandler.cv_queue.empty():
            tmp = (PropertyHandler.cv_queue.get())
            queue.put(tmp)
            PropertyHandler.cv_queue.put(tmp)
