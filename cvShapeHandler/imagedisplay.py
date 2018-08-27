import cv2
import numpy as np

from cvShapeHandler.gpuhandler import GPUHandler


class ImageDisplay:

    @staticmethod
    def display(img, window_name, size=(640, 480)):
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, GPUHandler.toUmat(cv2.resize(img, size)))

    @staticmethod
    def display_array(arr, window_name):
        stacked = np.hstack((arr))
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, stacked)

    @staticmethod
    def destroy(window_name):
        cv2.destroyWindow(window_name)