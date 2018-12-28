import io

import yaml


class PropertyHandler:
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
            "width": {"min": 0.1, "max": 100}
        },
        "preprocessing": {
            "morph": {"height": 8, "width": 20},
            "otsu": 0,
            "sobel": {"kernel": 3},
            "mask": {"lower": 0, "upper": 255}
        }
    }

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

            PropertyHandler.app_settings = {
                "camera": camera,
                "device": device,
                "restful": restful
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

            PropertyHandler.cv_settings = {
                "shape": shape,
                "char": char,
                "preprocessing": preprocessing
            }
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
