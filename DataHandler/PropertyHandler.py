import io

import yaml


class PropertyHandler:
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
        stream = io.open("conf.yml", 'r', encoding='utf8')
        configs = yaml.safe_load(stream)

        try:
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
        stream = io.open("detection.yml", 'r', encoding='utf8')
        configs = yaml.safe_load(stream)

        try:
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
    def save(filename, data):
        stream = io.open(filename, 'w', encoding='utf8')
        yaml.dump(data, stream, default_flow_style=False)
