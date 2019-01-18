import base64

import numpy as np
from flask import Flask, render_template, json, url_for
from flask_socketio import SocketIO

from Handlers.FrameHandler import FrameHandler
from Handlers.PropertyHandler import PropertyHandler
from cvlib.CvHelper import CvHelper


class Interface:

    def __init__(self):
        self.obj_queue = None
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.app.add_url_rule("/", "home", self.home)
        self.app.add_url_rule("/image", "image", self.image)
        self.app.add_url_rule("/video", "video", self.video)
        self.app.add_url_rule("/camera", "camera", self.camera)
        self.socketio = SocketIO(self.app)
        self.socketio.on('get-image', self.client_connect)
        self.socketio.on('add-image', self.add_image)
        self.socketio.on('shape-height', self.handle_shape_h)
        self.socketio.on('shape-width', self.handle_shape_w)
        self.socketio.on('shape-area', self.handle_shape_a)
        self.socketio.on('preprocessing-morph', self.preprocessing)
        self.socketio.on('char-area', self.char_area)
        self.socketio.on('char-width', self.char_width)
        self.socketio.on('char-height', self.char_height)
        self.socketio.on('angle', self.angle)
        self.socketio.on('mask', self.mask)
        self.socketio.on('char-morph', self.char_morph)
        self.socketio.on('save', self.save)

    def home(self):
        return render_template("index.html")

    def image(self):
        return render_template("image-view.html")

    def video(self):
        return render_template("video-view.html")

    def gen(self):
        while True:
            try:
                FrameHandler.get_all(self.obj_queue)
                o = self.obj_queue.get_nowait()
                if len(o) > 0:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + o.get_frame() + b'\r\n')
            except:
                pass

    def camera(self):
        return render_template("camera-view.html")

    def start(self, queue):
        self.obj_queue = queue
        print("Starting Rest Server")
        self.socketio.run(self.app, port=8080)

    def client_connect(self):
        print("Client Connected")
        FrameHandler.get_all(self.obj_queue)
        while not self.obj_queue.empty():
            obj = self.obj_queue.get_nowait()
            for x in obj:
                data = json.dumps({'name': x.get_name(), 'frame': FrameHandler.get_base64(x.get_frame()),
                                   'raw': FrameHandler.get_base64(x.get_raw())})
                print(data)
                self.socketio.emit('image', json=data)

    def add_image(self):
        image = base64.standard_b64decode(["image"])
        npimg = np.fromstring(image, np.uint8)
        mat = CvHelper.mat_encode(npimg, 100)

    def handle_shape_h(self, json):
        PropertyHandler.cv_settings["shape"]["height"] = json["height"]

    def handle_shape_w(self, json):
        PropertyHandler.cv_settings["shape"]["height"] = json["height"]

    def handle_shape_a(self, json):
        PropertyHandler.cv_settings["shape"]["area"] = json["area"]

    def preprocessing(self, json):
        PropertyHandler.cv_settings["preprocessing"]["morph"] = json["morph"]

    def char_area(self, json):
        PropertyHandler.cv_settings["char"]["area"] = json["area"]

    def char_width(self, json):
        PropertyHandler.cv_settings["char"]["width"] = json["width"]

    def char_height(self, json):
        PropertyHandler.cv_settings["char"]["height"] = json["height"]

    def angle(self, json):
        PropertyHandler.cv_settings["shape"]["angle"] = json["angle"]

    def mask(self, json):
        PropertyHandler.cv_settings["preprocessing"]["mask"] = json["mask"]

    def char_morph(self, json):
        PropertyHandler.cv_settings["char"]["morph"] = json["morph"]

    def save(self):
        print('Saving...')
        PropertyHandler.save("detection", PropertyHandler.cv_settings)
