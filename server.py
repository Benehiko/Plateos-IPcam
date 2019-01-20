from multiprocessing import Queue

from flask import Flask, render_template, json
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

    def __init__(self, q, cv_q):
        self.obj_queue = q
        self.cv_queue = cv_q


@app.route("/")
def home():
    return render_template("index.html")


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
    print("Client connected")
    # socketio.start_background_task(get_image)


# @app.route("/camera/<string:name>")
# def camera(name):
#     # return Response(gen(name), mimetype='multipart/x-mixed-replace; boundary=frame')
#     return render_template("camera-view.html")


def start(q, cv_q):
    QueueHandler(q, cv_q)
    print("Starting Rest Server")
    socketio.run(app, host="0.0.0.0", port=9000)


@socketio.on("get-image")
def get_image():
    FrameHandler.get_all(QueueHandler.obj_queue)
    obj = None
    while not QueueHandler.obj_queue.empty():
        obj = QueueHandler.obj_queue.get()

    if obj is not None:
        data = json.dumps({'name': obj[0], 'image': obj[1], 'output': obj[2]})
        socketio.emit('image', data)


@socketio.on("shape-height")
def handle_shape_h(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["height"] = data["height"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)  # cv_settings["shape"]["height"] = data["height"]


@socketio.on("shape-width")
def handle_shape_w(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["width"] = data["width"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("shape-area")
def handle_shape_a(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["area"] = data["area"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("preprocessing-morph")
def preprocessing(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["preprocessing"]["morph"] = data["morph"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)
    # PropertyHandler.cv_settings["preprocessing"]["morph"] = data["morph"]


@socketio.on("char-area")
def char_area(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["char"]["area"] = data["area"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-width")
def char_width(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["char"]["width"] = data["width"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-height")
def char_height(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["char"]["height"] = data["height"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("angle")
def angle(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["shape"]["angle"] = data["angle"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("mask")
def mask(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["preprocessing"]["mask"] = data["mask"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("char-morph")
def char_morph(data):
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        tmp["char"]["morph"] = data["morph"]
        QueueHandler.propertyhandler.set_cv_settings(tmp)


@socketio.on("save")
def save():
    print('Saving...')
    QueueHandler.propertyhandler.get_cv_settings(QueueHandler.cv_queue)
    while not QueueHandler.cv_queue.empty():
        tmp = QueueHandler.cv_queue.get()
        PropertyHandler.save("detection.yml", tmp)
    socketio.emit("saved")
