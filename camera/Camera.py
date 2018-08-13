import cv2, datetime
import numpy as np
import time

from urllib.request import urlopen
from threading import Thread
from cvShapeHandler.imgprocess import ImgProcess
from cvShapeHandler.imageprocessing import ImagePreProcessing
from cvShapeHandler.imagedisplay import ImageDisplay


class Camera:

    def __init__(self, ip, username, password, tess, backdrop):
        self.url = "http://" + ip + "/cgi-bin/api.cgi?cmd=Snap&channel=0&rs=wuuPhkmUCeI9WG7C&user=" + username + "&password=" + password

        # self.url = "rtsp://"+username+":"+password+"@"+ip+":554//h264Preview_01_main"
        # self.url = "rtmp://" + ip + "/bcs/channel0_main.bcs?channel=0&stream=0&user=" + username + "&password=" + password
        self.tess = tess
        self.img_process = ImgProcess(draw_enable=True)
        self.ip = ip
        self.backdrop = backdrop

    def start(self):
        print("Starting camera", self.ip)
        # bytes = ''
        while True:
            try:
                reader = urlopen(self.url)
                img_npy = np.array(bytearray(reader.read()), dtype=np.uint8)
                img = cv2.imdecode(img_npy, -1)

                rectangles, corrected = self.img_process.process(img)
                if rectangles is not None:
                    ImageDisplay.display(corrected, self.ip)
                    cropped = self.img_process.process_for_tess(img, rectangles)
                    pool = []
                    for i in cropped:
                        pool.append(Thread(target=self.tess.process(i)))

                    for i in pool:
                        i.start()

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cv2.destroyWindow(self.ip)
                    break

            except Exception as e:
                print(e)
                break

            finally:
                pass
        self.backdrop.callback_camera(self.ip)

    def resultime(self, results):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        for tmp in results:
            text, image = tmp
            print(text)
            ImagePreProcessing.save(image, filename)

    def get_ip(self):
        return self.ip
