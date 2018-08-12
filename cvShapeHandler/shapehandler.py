from cvShapeHandler.imageprocessing import ImagePreProcessing
from cvShapeHandler.imagedisplay import ImageDisplay

import logging
import numpy as np
import cv2


class ShapeHandler:

    def __init__(self, img):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.img = img
        self.contours = None

    def findcontours(self):


        processed = ImagePreProcessing.process_for_shape_detection_bright_backlight(self.img)
        ImageDisplay.display(processed, "Processed")

        #cv2.imshow("Testing result", processed)

        __, contours, hierarchy = cv2.findContours(processed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        self.contours = contours
        # cnts = contours[0] if imutils.is_cv2() else contours[1]
        return contours

    def polygontest(self, cnt_array, rect):
        count = 0
        ((x, y), (w, h), angle) = rect
        pnt_array = [(x, y), (x + w, y), (x, y - h), (x + w, y - h)]
        for cnt in cnt_array:
            for pnt in pnt_array:
                if cv2.pointPolygonTest(cnt, pnt, False) > -1:
                    count += 1
            if count == 4:
                rect_area = w * h  # cv2.contourArea(pnt_array)
                cnt_area = cv2.contourArea(cnt)
                if cnt_area > rect_area:
                    # print("Point inside contour!")
                    return True
        return False

    def get_approx(self, cnt):
        epsilon = 0.01 * cv2.arcLength(cnt, False)
        approx = cv2.approxPolyDP(cnt, epsilon, False)
        return approx

    def get_rotated_rect(self, approx):
        rect  = cv2.minAreaRect(approx)
        #((x, y), (w, h), angle) = rect
        return rect

    def in_scope_percentage(self, rect, area):
        ((x, y), (w, h), angle) = rect
        img_area, img_width, img_height = self.getAreaWidthHeight()
        p_a = (area * 100) / img_area
        p_w = w * 100 / img_width
        p_h = h * 100 / img_height
        if 0.12 <= p_a <= 5 and p_h <= 60 and p_w <= 60:
            #if (0 >= angle >= -30 or -150 >= angle >= -180) or (0 <= angle <= 30 or 150 <= angle <= 180):
            return True
        return False

    def getRectangles(self, contours):

        arrrect = []
        box_rect = []
        cnt_cache = []
        for cnt in contours:
            # Contour
            approx = self.get_approx(cnt)

            area = cv2.contourArea(approx)
            rect = self.get_rotated_rect(approx)

            # Some calculations
            if self.in_scope_percentage(rect, area):
                cnt_cache.append(cnt)

        cnt_cache = [x for x in cnt_cache if
                     not self.polygontest(cnt_cache, self.get_rotated_rect(self.get_approx(x)))]  # Keep element if it is not False

        for cnt in cnt_cache:
            approx = self.get_approx(cnt)
            rect = self.get_rotated_rect(approx)
            arrrect.append(rect)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            box_rect.append(box)

        return arrrect, box_rect

    def getCharacters(self, contours):
        arrrect = []
        box_rect = []

        for cnt in contours:
            approx = self.get_approx(cnt)
            rect = self.get_rotated_rect(approx)
            arrrect.append(rect)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            box_rect.append(box)

        return arrrect, box_rect


    def isDuplicate(self, arrrect, box):
        for tmp in arrrect:
            return box == tmp

    def getAreaWidthHeight(self):
        # print("DEBUG: Getting img area with shape property")
        imgHeight, imgWidth, imgChannels = self.img.shape
        imgArea = (imgHeight) * (imgWidth)
        return imgArea, imgWidth, imgHeight
