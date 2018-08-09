import cv2, datetime
import numpy as np
import requests

from threading import Thread
from cvShapeHandler.imgprocess import ImgProcess
from cvShapeHandler.imageprocessing import ImagePreProcessing


class Camera:

    def __init__(self, ip, username, password, tess):
        self.url = "rtmp://" + ip + "/bcs/channel0_main.bcs?channel=0&stream=0&user=" + username + "&password=" + password
        self.tess = tess
        self.img_process = ImgProcess(draw_enable=True)
        self.ip = ip

    def start(self):
        print("Starting camera", self.ip)
        while True:
            f_counter = 0
            try:
                #try:
                    # self.stream = requests.get(self.url, stream=True)
                    # bytes += self.stream.raw.read(1024)
                    # a = bytes.find('\xff\xd8')
                    # b = bytes.find('\xff\xd9')
                    # if a != -1 and b != -1:
                    #     jpg = bytes[a:b + 2]
                    #     bytes = bytes[b + 2:]
                    #     img = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)

                camera = cv2.VideoCapture(self.url)
                camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                while camera.isOpened():

                    # print(camera.get(cv2.CAP_PROP_BUFFERSIZE))
                    ret, frame = camera.read()
                    if ret:
                        drawn, rectangles = self.img_process.process(frame)
                        if drawn is not None:
                            cv2.namedWindow(self.ip, cv2.WINDOW_NORMAL)
                            cv2.imshow(self.ip, cv2.resize(drawn, (1296, 768)))
                            if f_counter == 100:
                                cropped = self.img_process.process_for_tess(frame, rectangles)
                                f_counter = 0
                                pool = []
                                for i in cropped:
                                    pool.append(Thread(target=self.tess.process(i)))

                                for i in pool:
                                    i.start()

                            f_counter += 1

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cv2.destroyWindow(self.ip)
                    break


            except Exception as e:
                print(e)

            finally:
                if isinstance(camera, cv2.VideoCapture):
                    camera.release()

    def resultime(self, results):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        for tmp in results:
            text, image = tmp
            print(text)
            ImagePreProcessing.save(image, filename)
