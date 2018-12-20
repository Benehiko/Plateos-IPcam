import math

import cv2
import numpy as np

from DataHandler.PropertyHandler import PropertyHandler
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
        k = (int(PropertyHandler.cv_settings["char"]["morph"]["min"]),
             int(PropertyHandler.cv_settings["char"]["morph"]["max"]))
        d = data.copy()
        morph = CvHelper.morph(d, gradient_type=CvEnums.MORPH_DILATE, kernel_shape=CvEnums.K_RECTANGLE,
                               kernel_size=k, iterations=2)
        diff = CvHelper.subtract(morph, d)
        diff = CvHelper.inverse(diff)
        # morph = CvHelper.morph(diff, gradient_type=CvEnums.MORPH_DILATE, kernel_shape=CvEnums.K_RECTANGLE,
        #                        kernel_size=(5, 5), iterations=1)
        return diff

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
        try:
            values = PropertyHandler.cv_settings["preprocessing"]
            illum = ImageUtil.illumination_correction(image.copy())
            mask_setup = PropertyHandler.cv_settings["preprocessing"]["mask"]
            lower = np.array(int(mask_setup["lower"]))
            upper = np.array(int(mask_setup["upper"]))
            img = CvHelper.greyscale(illum)
            mask = cv2.inRange(img, lower, upper)
            # blur = CvHelper.gaussian_blur(mask, kernel_size=3)
            # sobelx = CvHelper.sobel(mask, kernel_size=3)  # int(values["sobel"]["kernel"]))
            otsu = CvHelper.adaptive_thresholding(mask, int(values["otsu"]))
            morph = CvHelper.morph(otsu, CvEnums.MORPH_CLOSE,
                                   kernel_size=(int(values["morph"]["width"]), int(values["morph"]["height"])),
                                   kernel_shape=CvEnums.K_ELLIPSE,
                                   iterations=2)

            # CvHelper.display("ShapeDetect", morph.copy(), size=(640, 480))
            return morph
        except Exception as e:
            print(e)
            pass
        return None

    @staticmethod
    def fix_brightness(mat):
        img = mat.copy()
        dilate = CvHelper.dilate(img.copy(), kernel_size=3)
        blur = CvHelper.median_blur(dilate, 21)
        diff = 255 - CvHelper.normalise(img, blur)
        normalised = diff.copy()
        normalised = CvHelper.normalise(diff, normalised)
        equ = CvHelper.equalise_hist(normalised, by_tile=True, tile_size=(1, 3))
        thresh = CvHelper.binarise(equ, 127, 0, type=CvEnums.THRESH_TRUNC)
        norm = CvHelper.normalise(thresh, thresh)
        # morph = CvHelper.morph(norm, gradient_type=CvEnums.MORPH_DILATE, kernel_shape=CvEnums.K_ELLIPSE, kernel_size=(1,3))
        blank = norm.copy()
        blank = CvHelper.morph(blank, gradient_type=CvEnums.MORPH_ERODE, kernel_size=(5, 5))
        blank = CvHelper.binarise(blank, 240, 255, CvEnums.THRESH_BINARY)
        inv = CvHelper.inverse(norm)
        result = CvHelper.subtract(inv, blank)
        equ = CvHelper.equalise_hist(result, by_tile=True, tile_size=(1, 3))
        # inv = CvHelper.inverse(inv)
        # thresh = CvHelper.otsu_binary(result, 0)
        # thresh = CvHelper.normalise(thresh, thresh)
        # adaptive = CvHelper.adaptive_thresholding(thresh)
        return equ

    @staticmethod
    def auto_crop(image_source, rectangle):
        """Return a rotated and cropped version of the source image"""

        # First slightly crop edge - some images had a rogue 2 pixel black edge on one side
        init_crop = 10
        h, w = image_source.shape[:2]
        image_source = image_source[init_crop:init_crop + (h - init_crop * 2),
                       init_crop:init_crop + (w - init_crop * 2)]
        # Add back a white border
        image_source = CvHelper.copy_make_border(image_source, sides=(5, 5, 5, 5), border_type=CvEnums.BORDER_CONSTANT,
                                                 border_colour=CvEnums.COLOUR_BLACK)
        centre, dimensions, theta = rectangle

        width = int(dimensions[0]) + 20
        height = int(dimensions[1]) + 10

        box = CvHelper.box_points(rectangle)

        M = CvHelper.moments(box)
        cx = int(M['m10'] / M['m00']) - 10
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
        rotated = CvHelper.warp_affine(mat, M, (w, h), flags=CvEnums.MAT_INTER_CUBIC,
                                       border_mode=CvEnums.BORDER_REPLICATE)
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
    async def char_roi(mat, rectangle, char_bounds, char_points):
        tmp = mat.copy()
        potential_plate = ImageUtil.auto_crop(tmp, rectangle)
        # norm_illum = ImageUtil.illumination_correction(potential_plate)

        # Grey Image -> Thresh
        greyscale = CvHelper.greyscale(potential_plate)
        deskew = ImageUtil.deskew(greyscale)
        blur = CvHelper.gaussian_blur(deskew, kernel_size=5)
        thresh = CvHelper.otsu_binary(blur, 0)

        contours, __ = ContourHandler.find_contours(thresh.copy(), ret_mode=CvEnums.RETR_LIST,
                                                    approx_method=CvEnums.CHAIN_APPROX_NONE)

        if len(contours) > 0:
            height, width, __ = potential_plate.shape
            roi, boxs = ContourHandler().get_characters_roi(contours, mat_width=width, mat_height=height,
                                                            char_bounds=char_bounds, points=char_points)
            if 2 <= len(roi) <= 12:
                drawn = CvHelper.draw_boxes(potential_plate, boxs, thickness=1, colour=CvEnums.COLOUR_GREEN)
                return thresh, drawn

        return None, None

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

    @staticmethod
    def illumination_correction(mat):
        lab = CvHelper.bgr2lab(mat)
        l, a, b = CvHelper.split(lab)
        equ = CvHelper.equalise_hist(l, by_tile=True, tile_size=(3, 3))
        img = CvHelper.merge((equ, a, b))
        result = CvHelper.lab2bgr(img)
        return result

    @staticmethod
    def shaddow_correction(mat):
        split = CvHelper.split(mat)
        norm = []
        for s in split:
            dilate = CvHelper.dilate(s, kernel_size=(7, 7))
            bg_img = CvHelper.median_blur(dilate, kernel_size=21)
            diff_img = 255 - CvHelper.absdiff(s, bg_img)
            norm_img = CvHelper.normalise(diff_img, diff_img)
            norm.append(norm_img)
        return CvHelper.merge(norm)

    @staticmethod
    def noise_correction(mat):
        tmp = mat.copy()
        dilate = CvHelper.dilate(tmp, kernel_size=(7, 1))
        erode = CvHelper.erode(dilate, kernel_size=(7, 1))
        morph = CvHelper.morph(erode, CvEnums.MORPH_CLOSE, kernel_shape=CvEnums.K_RECTANGLE, kernel_size=(7, 1))
        thresh = CvHelper.binarise(morph, thresh=230, type=CvEnums.THRESH_BINARY)
        img = 255 - mat
        line = 255 - thresh
        text = img - line
        # bilateral = CvHelper.bilateralFilter(text)
        CvHelper.display("Noise Correction", text)
        return text
