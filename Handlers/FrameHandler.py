import base64
import sys
from io import BytesIO
from threading import Thread

import cv2
import numpy as np
from PIL import Image

from cvlib.ImageUtil import ImageUtil


class FrameHandler:
    obj = set()

    @staticmethod
    def add_obj(queue):
        try:
            print("Adding Camera")
            val = queue.get()
            print(val)
            if len(val) > 0:
                FrameHandler.obj.add(val)
        except Exception as e:
            print("Adding Camera error", e)
            sys.exc_traceback()

    @staticmethod
    def search(name):
        for x in FrameHandler.obj:
            if x.get_name() == name:
                return x
        return None

    @staticmethod
    def get_base64(mat):
        if mat is not None:
            compress = ImageUtil.compress(mat, max_w=640, quality=20)
            retval, buffer = cv2.imencode('.jpg', compress)
            b64 = base64.standard_b64encode(buffer)
            return b64
        return ''

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
        queue.put(FrameHandler.obj)

    @staticmethod
    def remove(queue):
        while not queue.empty():
            val = queue.get_nowait()
            FrameHandler.obj.discard(val)
