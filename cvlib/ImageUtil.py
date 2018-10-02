import datetime
import math

import numpy as np

from cvlib.ContourHandler import ContourHandler
from cvlib.CvEnums import CvEnums
from cvlib.CvHelper import CvHelper


class ImageUtil:

    @staticmethod
    def compress(mat, max_w=1270, max_h=720, quality=65):
        resized = CvHelper.resize(mat, new_width=max_w, new_height=max_h, interpolation=CvEnums.MAT_INTER_AREA)
        encoded = CvHelper.mat_encode(resized, quality)
        decoded = CvHelper.mat_decode(encoded)
        return decoded

    @staticmethod
    async def process_for_tess(data):
        data = data.copy()
        #(h, w) = data.shape[:2]
        # if h < 760 or w < 1296:
        #     data = CvHelper.resize(data, new_width=1296, new_height=760)
        #darken = CvHelper.adjust_gamma(data, 2.5)
        result = CvHelper.inverse(data)
        return result


    """
    Too Experimental for now
    @staticmethod
    def process_change(historic_images, present):
        results = []
        tmp_p = present.copy()
        resized_present = CvHelper.resize(tmp_p, int(present.shape[0] / 4))
        gray_present = CvHelper.gaussian_blur(CvHelper.greyscale(resized_present))

        for historic in historic_images:
            img, __ = historic
            tmp = CvHelper.resize(img, int(img.shape[0] / 4))
            gray_hist = CvHelper.gaussian_blur(CvHelper.greyscale(tmp))
            (score, diff) = compare_ssim(gray_hist, gray_present, full=True)
            diff = (diff * 255).astype("uint8")
            thresh = CvHelper.resize(CvHelper.adaptive_thresholding(diff), new_width=int(present.shape[0]))
            contours, __ = ContourHandler.find_contours(thresh, ret_mode=CvEnums.RETR_EXTERNAL)
            if len(contours) > 0:
                rectangles, box_rectangles, angles = ContourHandler.get_rectangles(contours, present, area_bounds=(1, 10), min_point=(1, 1), max_point=(60, 60))
                if len(rectangles) > 0:
                    objs = CvHelper.draw_boxes(mat=present, arr_box_pnts=box_rectangles, colour=CvEnums.COLOUR_GREEN, thickness=5)
                    CvHelper.display("Objects", objs)
                    results += rectangles

        return results
        """

    @staticmethod
    def process_for_shape_detection_bright_backlight(image):
        img = CvHelper.get_umat(image.copy())
        greyscale = CvHelper.greyscale(img)
        bright = CvHelper.adjust_gamma(greyscale, 2.5)
        blur = CvHelper.gaussian_blur(bright, kernel_size=5)
        thresh = CvHelper.get_mat(CvHelper.adaptive_thresholding(blur, CvEnums.THRESH_MEAN))
        otsu = CvHelper.binarise(thresh, 127)
        return otsu

    @staticmethod
    def auto_crop(image_source, rectangle):
        """Return a rotated and cropped version of the source image"""

        # First slightly crop edge - some images had a rogue 2 pixel black edge on one side
        init_crop = 10
        h, w = image_source.shape[:2]
        image_source = image_source[init_crop:init_crop + (h - init_crop * 2),
                       init_crop:init_crop + (w - init_crop * 2)]
        # Add back a white border
        image_source = CvHelper.copy_make_border(image_source, sides=(5, 5, 5, 5), border_type=CvEnums.BORDER_CONSTANT, border_colour=CvEnums.COLOUR_BLACK)
        centre, dimensions, theta = rectangle

        width = int(dimensions[0]*2)
        height = int(dimensions[1]*2)

        box = CvHelper.box_points(rectangle)

        M = CvHelper.moments(box)
        cx = int(M['m10'] / M['m00']) - 5
        cy = int(M['m01'] / M['m00']) - 5

        image_patch = ImageUtil.sub_image(image_source, (cx, cy), theta + 90, height, width)
        return image_patch

    @staticmethod
    def deskew(mat):
        """
        Deskew a greyscale mat by using the contours retrieved from threshed image
        :param mat: greyscale image
        :return:
        """
        # grab the (x, y) coordinates of all pixel values that
        # are greater than zero, then use these coordinates to
        # compute a rotated bounding box that contains all
        # coordinates
        inverse = CvHelper.inverse(mat.copy())
        thresh = CvHelper.otsu_binary(inverse)

        coords = np.column_stack(np.where(thresh > 0))
        angle = CvHelper.min_area_rect(coords)[-1]

        # the `cv2.minAreaRect` function returns values in the
        # range [-90, 0); as the rectangle rotates clockwise the
        # returned angle trends to 0 -- in this special case we
        # need to add 90 degrees to the angle
        if angle < -45:
            angle = -(90 + angle)

        # otherwise, just take the inverse of the angle to make
        # it positive
        else:
            angle = -angle

        # rotate the image to deskew it
        (h, w) = mat.shape[:2]
        center = (w // 2, h // 2)
        M = CvHelper.rotation_matrix_2D(center, angle, 1.0)
        rotated = CvHelper.warp_affine(mat, M, (w, h), flags=CvEnums.MAT_INTER_CUBIC, border_mode=CvEnums.BORDER_REPLICATE)
        return rotated

    @staticmethod
    def sub_image(image, center, theta, width, height):
        """
        :param image: source image
        :param center: (x,y) tuple for the centre point
        :param theta: angle of the rectangle
        :param width:
        :param height:
        :return:
        """

        if 45 < theta <= 90:
            theta = theta - 90
            width, height = height, width

        theta *= math.pi / 180  # convert to rad
        v_x = (math.cos(theta), math.sin(theta))
        v_y = (-math.sin(theta), math.cos(theta))
        s_x = center[0] - v_x[0] * (width / 2) - v_y[0] * (height / 2)
        s_y = center[1] - v_x[1] * (width / 2) - v_y[1] * (height / 2)
        mapping = np.array([[v_x[0], v_y[0], s_x], [v_x[1], v_y[1], s_y]])

        return CvHelper.warp_affine(image, mapping, (width, height), flags=CvEnums.MAT_WARP_INVERSE_MAP,
                              border_mode=CvEnums.BORDER_REPLICATE)

    @staticmethod
    async def char_roi(mat, rectangle):
        tmp = mat.copy()
        potential_plate = ImageUtil.auto_crop(tmp, rectangle)
        greyscale = CvHelper.greyscale(potential_plate)
        deskew = CvHelper.get_umat(ImageUtil.deskew(greyscale))
        #deskew = CvHelper.adjust_gamma(deskew, gamma=2.5)
        # now = datetime.datetime.now().strftime('%H')
        # if '19' > now < '06':
        #     deskew = CvHelper.adjust_gamma(deskew, gamma=2.5)
        otsu = CvHelper.get_mat(CvHelper.otsu_binary(deskew, 240))
        canny = CvHelper.canny_thresholding(otsu.copy())
        contours, __ = ContourHandler.find_contours(canny.copy(), ret_mode=CvEnums.RETR_LIST, approx_method=CvEnums.CHAIN_APPROX_SIMPLE)

        if len(contours) > 0:
            height, width, __ = potential_plate.shape
            roi, boxs = ContourHandler().get_characters_roi(contours, mat_width=width, mat_height=height)
            if 2 <= len(roi) <= 12:
                #results.append((rectangle, roi))
                return otsu
        return None

    @staticmethod
    def rotate_image(img, angle):
        height, width = img.shape[:2]
        image_center = (width / 2, height / 2)

        rotation_mat = CvHelper.rotation_matrix_2D(image_center, angle, 1)

        radians = math.radians(angle)
        sin = math.sin(radians)
        cos = math.cos(radians)
        bound_w = int((height * abs(sin)) + (width * abs(cos)))
        bound_h = int((height * abs(cos)) + (width * abs(sin)))

        rotation_mat[0, 2] += ((bound_w / 2) - image_center[0])
        rotation_mat[1, 2] += ((bound_h / 2) - image_center[1])

        rotated_mat = CvHelper.warp_affine(img, rotation_mat, (bound_w, bound_h))
        return rotated_mat