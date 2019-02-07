from multiprocessing import Queue
from threading import Thread
from time import sleep

from flask import Flask, render_template, json as j
from flask_socketio import SocketIO

from Handlers.FrameHandler import FrameHandler
from Handlers.PropertyHandler import PropertyHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
obj_queue = Queue()


class QueueHandler:
    obj_queue = Queue()
    cv_queue = Queue()
    propertyhandler = PropertyHandler()

    def __init__(self, q: Queue, cv_q: Queue):
        self.obj_queue = q
        self.cv_queue = cv_q
        Thread(target=self.clean).start()

    def clean(self):
        while True:
            while not self.obj_queue.empty():
                self.obj_queue.get_nowait()
            FrameHandler.clean()
            sleep(10)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/image")
def image():
    return render_template("image-view.html")


@app.route("/video")
def video():
    return render_template("video-view.html")


@socketio.on("connected")
def client_connected():
    print("Client connected")


def start(q, cv_q):
    QueueHandler(q, cv_q)
    print("Starting Rest Server")
    socketio.run(app, host="0.0.0.0", port=9000)


@socketio.on("get-image")
def get_image():
    FrameHandler.get_all(QueueHandler.obj_queue)
    obj = None
    while not QueueHandler.obj_queue.empty():
        obj = QueueHandler.obj_queue.get_nowait()

    if obj is not None:
        if type(obj[1]) is str:
            data = j.dumps({'name': obj[0], 'image': obj[1]})
            socketio.emit('image', data)


@socketio.on("shape-height")
def handle_shape_h(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["shape"]["height"] = data["height"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)  # cv_settings["shape"]["height"] = data["height"]


@socketio.on("shape-width")
def handle_shape_w(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["shape"]["width"] = data["width"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("shape-area")
def handle_shape_a(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["shape"]["area"] = data["area"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("preprocessing-morph-height")
def preprocessing(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["preprocessing"]["morph"]["height"] = data["morph"]["height"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)
    # PropertyHandler.cv_settings["preprocessing"]["morph"] = data["morph"]


@socketio.on("preprocessing-morph-width")
def preprocess_morph_width(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        if tmp is not None:
            tmp["preprocessing"]["morph"]["width"] = data["morph"]["width"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-area")
def char_area(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["char"]["area"] = data["area"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-width")
def char_width(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["char"]["width"] = data["width"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-height")
def char_height(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["char"]["height"] = data["height"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-morph")
def char_morph(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["char"]["morph"] = data["char"]["morph"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("angle")
def angle(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["shape"]["angle"] = data["angle"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("mask")
def mask(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["preprocessing"]["mask"] = data["mask"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("otsu")
def char_morph(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["preprocessing"]["otsu"] = data["otsu"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("erode")
def erode(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            tmp["preprocessing"]["erode"] = data["erode"]
            QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("save")
def save():
    print('Saving...')
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get_nowait()
        if tmp is not None:
            PropertyHandler.save("detection.yml", tmp)
            socketio.emit("saved")
