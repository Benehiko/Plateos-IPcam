from asyncio import sleep
from multiprocessing import Queue
from threading import Thread, Lock

from flask import Flask, render_template, json, Response
from flask_socketio import SocketIO

from Handlers.FrameHandler import FrameHandler
from Handlers.PropertyHandler import PropertyHandler

async_mode = None
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)
obj_queue = Queue()
thread = None
thread_lock = Lock()


class QueueHandler:
    obj_queue = Queue()
    cv_queue = Queue()
    propertyhandler = PropertyHandler()

    def __init__(self, q, cv_q):
        self.obj_queue = q
        self.cv_queue = cv_q


@app.route("/")
def home():
    return render_template("index.html", async_mode=socketio.async_mode)


@app.route("/image")
def image():
    return render_template("image-view.html")


@app.route("/video")
def video():
    return render_template("video-view.html")


def gen(name):
    while True:
        FrameHandler.get_all(QueueHandler.obj_queue)
        while not QueueHandler.obj_queue.empty():
            obj = QueueHandler.obj_queue.get()
            if obj[0] == name:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + obj[1] + b'\r\n')


@socketio.on("connected")
def client_connected():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(get_image)


@app.route("/camera/<string:name>")
def camera(name):
    # return Response(gen(name), mimetype='multipart/x-mixed-replace; boundary=frame')
    return render_template("camera-view.html")


def start(q, cv_q):
    QueueHandler(q, cv_q)
    print("Starting Rest Server")
    socketio.run(app, port=9000)


def get_image():
    while True:
        FrameHandler.get_all(QueueHandler.obj_queue)
        while not QueueHandler.obj_queue.empty():
            obj = QueueHandler.obj_queue.get()
            data = json.dumps({'name': obj[0], 'image': obj[1], 'output': obj[2]})
            socketio.emit('image', data)
        sleep(1)


@socketio.on("shape-height")
def handle_shape_h(data):
    print(data)
    PropertyHandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["height"] = data["height"]
        PropertyHandler.set_cv_settings(tmp)  # cv_settings["shape"]["height"] = data["height"]


@socketio.on("shape-width")
def handle_shape_w(data):
    PropertyHandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["width"] = data["width"]
        PropertyHandler.set_cv_settings(tmp)


@socketio.on("shape-area")
def handle_shape_a(data):
    PropertyHandler.cv_settings["shape"]["area"] = data["area"]


@socketio.on("preprocessing-morph")
def preprocessing(data):
    print(data)
    q = Queue()
    QueueHandler.propertyhandler.get_cv_settings(q)
    while not q.empty():
        tmp = q.get()
        print(data["morph"])
        tmp["preprocessing"]["morph"] = data["morph"]
        PropertyHandler.set_cv_settings(tmp)
    # PropertyHandler.cv_settings["preprocessing"]["morph"] = data["morph"]


@socketio.on("char-area")
def char_area(data):
    PropertyHandler.cv_settings["char"]["area"] = data["area"]


@socketio.on("char-width")
def char_width(data):
    PropertyHandler.cv_settings["char"]["width"] = data["width"]


@socketio.on("char-height")
def char_height(data):
    PropertyHandler.cv_settings["char"]["height"] = data["height"]


@socketio.on("angle")
def angle(data):
    PropertyHandler.cv_settings["shape"]["angle"] = data["angle"]


@socketio.on("mask")
def mask(data):
    PropertyHandler.cv_settings["preprocessing"]["mask"] = data["mask"]


@socketio.on("char-morph")
def char_morph(data):
    PropertyHandler.cv_settings["char"]["morph"] = data["morph"]


@socketio.on("save")
def save():
    print('Saving...')
    PropertyHandler.save("detection", PropertyHandler.cv_settings)
