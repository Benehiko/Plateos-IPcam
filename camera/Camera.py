import cv2, datetime
import threading
from tess.tesseract import Tess
from cvShapeHandler.process import Process
from cvShapeHandler.imageprocessing import ImagePreProcessing


class Camera(threading.Thread):

    def __init__(self, ip, username, password):
        threading.Thread.__init__(self)
        self.url = "rtmp://"+ip+"/bcs/channel0_main.bcs?channel=0&stream=0&user="+username+"&password="+password
        self.tess = Tess()
        self.process = Process(draw_enable=True)
        #cv2.namedWindow(self.url, cv2.WINDOW_NORMAL)

        try:
            self.camera = cv2.VideoCapture(self.url)
        except Exception as e:
            print(e)

    def run(self):
        print("Starting camera")
        try:
            counter = 0
            while self.camera.isOpened():
                if counter == 100:
                    counter = 0
                    ret, frame = self.camera.read()
                    if ret:
                        drawn, rectangles = self.process.process(frame)
                        if drawn is not None:
                            cropped = self.process.process_for_tess(frame, rectangles)
                            cv2.imshow(self.url, cv2.resize(drawn, (1296, 768)))
                            print(self.tess.process(cropped, self))

                counter += 1

                if cv2.waitKey(25) & 0xFF == ord('q'):
                    cv2.destroyWindow(self.url)
                    break

        except Exception as e:
            print(e)

        finally:
            self.camera.release()


    def callback(self, img):
        filename = "cache/" + datetime.datetime.now().strftime("%Y-%m-%d")
        ImagePreProcessing.save(img, filename)