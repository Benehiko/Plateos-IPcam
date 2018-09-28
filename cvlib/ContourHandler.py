import asyncio

import cv2
import numpy as np
import multiprocessing as mp
from cvlib.CvEnums import CvEnums


class ContourHandler:

    @staticmethod
    def find_contours(mat, ret_mode=CvEnums.RETR_LIST, approx_method=CvEnums.CHAIN_APPROX_SIMPLE):
        """
        https://docs.opencv.org/3.0.0/d4/d73/tutorial_py_contours_begin.html
        This function keeps the image source intact
        :param approx_method:
        :param ret_mode:
        :param mat:
        :return:
        """
        __, contours, hierarchy = cv2.findContours(mat.copy(), ret_mode.value, approx_method.value)
        return contours, hierarchy

    @staticmethod
    def polygon_test(cnt_array, rect):
        """
        Test for shapes duplicates (inside bigger shapes etc.)
        Test for rectangles
        :param cnt_array:
        :param rect:
        :return:
        """
        count = 0
        ((x, y), (w, h), angle) = rect
        pnt_array = [(x, y), (x + w, y), (x, y - h), (x + w, y - h)]
        for cnt in cnt_array:
            for pnt in pnt_array:
                if cv2.pointPolygonTest(cnt, pnt, False) > -1:
                    count += 1
            if count == 4:
                rect_area = w * h
                cnt_area = cv2.contourArea(cnt)
                if cnt_area > rect_area:
                    return True
        return False

    @staticmethod
    def get_approx(cnt):
        epsilon = 0.01 * cv2.arcLength(cnt, False)
        approx = cv2.approxPolyDP(cnt, epsilon, False)
        return approx

    @staticmethod
    def get_rotated_rect(approx):
        rect = cv2.minAreaRect(approx)
        return rect

    @staticmethod
    def in_scope_percentage(rect, rect_area, size, area_bounds=(0.5, 5), min_point=(10, 10), max_point=(60, 60)):
        """
        Check rectangle size against image
        :param size: tuple
        :param max_point:
        :param min_point:
        :param area_bounds:
        :param rect:
        :param rect_area:
        :return:
        """
        rect_min_area, rect_max_area = area_bounds
        width_min, height_min = min_point
        width_max, height_max = max_point

        (__, (w, h), angle) = rect
        img_area, img_width, img_height = ContourHandler.get_area_width_height(size)
        r_area = (rect_area * 100) / img_area
        r_width = w * 100 / img_width
        r_height = h * 100 / img_height

        #0.5 , 10 , 60, 60
        return (rect_min_area <= r_area <= rect_max_area) and (height_min <= r_height <= height_max) and (width_min <= r_width <= width_max)

    @staticmethod
    def in_correct_angle(rect):
        """
        Correct OpenCV angles to 180 degree plain
        :param rect:
        :return:
        """
        (__, (w, h), angle) = rect
        if w < h:
            angle = angle - 90
        return angle

    @staticmethod
    def correct_ratio(rect):
        """
        Remove 'tall' rectangles
        Only 'wide' rectangles are kept
        :param rect:
        :return:
        """
        (__, (w, h), angle) = rect
        ratio_w_h = (w / h)
        ratio_h_w = (h / w)
        return 0.8 <= ratio_w_h <= 20 or 0.1 <= ratio_h_w <= 1.5

    @staticmethod
    def get_rectangles(contours, mat_width, mat_height, area_bounds=(0.5, 5), min_point=(10, 10), max_point=(60, 60)):
        """
        Get rectangles from contours
        :param mat_height:
        :param mat_width:
        :param contours:
        :param area_bounds: tuple indicating the (min, max) of the acceptable area
        :param min_point: tuple of minimum threshold for (width_min, height_min)
        :param max_point: tuple of maximum threshold for (width_max, height_max)
        :return: rectangles
        """
        rect_arr = []
        cnt_cache = []
        for cnt in contours:
            approx = ContourHandler.get_approx(cnt)
            area = cv2.contourArea(approx)
            rect = ContourHandler.get_rotated_rect(approx)
            if ContourHandler.in_scope_percentage(rect, area, size=(mat_width, mat_height), area_bounds=area_bounds, min_point=min_point, max_point=max_point):
                cnt_cache.append(cnt)

        # Keep element if it is not False
        cnt_cache = [x for x in cnt_cache if
                     not ContourHandler.polygon_test(cnt_cache, ContourHandler.get_rotated_rect(ContourHandler.get_approx(x)))]


        box_corrected = []
        angles = []

        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        pool = [asyncio.ensure_future(ContourHandler.contour_helper(cnt), loop=event_loop) for cnt in cnt_cache]

        resultset = event_loop.run_until_complete(asyncio.gather(*pool))
        for r in resultset:
            rect, box, ang = r
            rect_arr.append(rect)
            box_corrected.append(box)
            angles.append(ang)

        rect_arr = [x for x in rect_arr if x is not None]
        box_corrected = [x for x in box_corrected if x is not None]
        angles = [x for x in angles if x is not None]
        event_loop.close()
        # pool = mp.Pool(processes=len(cnt_cache))
        # [pool.apply_async(ContourHandler.contour_helper(cnt, rect_arr, box_corrected, angles)) for cnt in cnt_cache]
        # pool.close()
        # pool.join()

        return rect_arr, box_corrected, angles

    @staticmethod
    async def contour_helper(cnt):
        approx = ContourHandler.get_approx(cnt)
        rect = ContourHandler.get_rotated_rect(approx)
        angle = ContourHandler.in_correct_angle(rect)
        if angle > -30 or angle < -100 or angle < -150:
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            if ContourHandler.correct_ratio(rect):
                ((x, y), __, __) = rect
                x = int(x)
                y = int(y)
                return rect, box, (angle, (x, y))
        return None, None, None
        #return rect_arr, box_corrected, angles

    @staticmethod
    def get_characters_roi(contours, mat_width, mat_height):
        rect_array = []
        box_rect = []

        cnt_cache = []
        for cnt in contours:
            approx = ContourHandler.get_approx(cnt)
            area = cv2.contourArea(approx)
            rect = ContourHandler.get_rotated_rect(approx)

            if ContourHandler.in_scope_percentage(rect, area, size=(mat_width, mat_height), area_bounds=(0.5, 10), min_point=(1, 1),
                                                  max_point=(80, 80)):
                cnt_cache.append(cnt)

        # Keep element if it is not False
        #cnt_cache = [x for x in cnt_cache if not ContourHandler.polygon_test(cnt_cache, ContourHandler.get_rotated_rect(ContourHandler.get_approx(x)))]

        for cnt in cnt_cache:
            approx = ContourHandler.get_approx(cnt)
            rect = ContourHandler.get_rotated_rect(approx)
            rect_array.append(rect)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            box_rect.append(box)

        return rect_array, box_rect

    @staticmethod
    def is_duplicate(rect_array, box):
        """
        Check if the same rectangle has been found
        :param rect_array:
        :param box:
        :return:
        """
        for tmp in rect_array:
            return box == tmp

    @staticmethod
    def get_area_width_height(size):
        """
        Get the area, width, height of a mat image
        :param size:
        :return:
        """
        img_width, img_height = size
        img_area = img_height * img_width
        return img_area, img_width, img_height
