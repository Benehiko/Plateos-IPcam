import base64
from io import BytesIO
from multiprocessing import Queue
from threading import Thread

import cv2
import numpy as np
from PIL import Image

from cvlib.ImageUtil import ImageUtil


class FrameHandler:
    obj = []
    queues = Queue()

    @staticmethod
    def add_obj(val):
        try:
            if val is not None:
                tmp = [val[0], FrameHandler.get_base64(val[1])]
                FrameHandler.obj.append(tmp)
                FrameHandler.queues.put(tmp)
        except Exception as e:
            print("Adding Camera error\n", e)

    @staticmethod
    def search(name):
        for x in FrameHandler.obj:
            if x.get_name() == name:
                return x
        return None

    @staticmethod
    def get_base64(mat):
        if mat is not None:
            compress = ImageUtil.compress(mat, max_w=480, quality=80)
            retval, buffer = cv2.imencode('.jpg', compress)
            b64 = base64.standard_b64encode(buffer)
            return b64.decode('utf-8')
        return ""

    @staticmethod
    def get_blob(mat):
        if mat is not None:
            image = Image.fromarray(np.uint8(mat))
            temp = BytesIO()
            image.save(temp, "JPEG", dpi=(600, 400))
            temp.seek(0)
            return temp
        return ''

    @staticmethod
    def start_obj():
        for x in range(0, FrameHandler.obj.__len__()):
            Thread(target=FrameHandler.obj[x].start).start()

    @staticmethod
    def get_all(queue):
        while not FrameHandler.queues.empty():
            obj = FrameHandler.queues.get()
            # image = Image.open(temp)
            queue.put([obj[0], obj[1]])
