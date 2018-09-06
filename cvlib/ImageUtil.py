import math
import pathlib
from datetime import datetime

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
    def process_for_tess(image, rectangles):
        images = []
        cropped_arr = ImageUtil.get_sub_images(image, rectangles)

        for crop in cropped_arr:
            grey = CvHelper.greyscale(crop)
            deskew = ImageUtil.deskew(grey)
            umat = CvHelper.get_umat(deskew)
            bright = CvHelper.adjust_gamma(umat, 2.0)
            dilate = CvHelper.dilate(bright, kernel_size=3, iterations=0)
            morph = CvHelper.morph(dilate, gradient_type=CvEnums.MORPH_OPEN, kernel_size=3,
                                   kernel_shape=CvEnums.K_ELLIPSE)
            otsu = CvHelper.get_mat(CvHelper.otsu_binary(morph, 240))
            images.append(otsu)

        return images

    @staticmethod
    def get_sub_images(image, rectangles):
        images = []
        tmp = image.copy()
        for rectangle in rectangles:
            cropped = ImageUtil.auto_crop(tmp, rectangle)
            if cropped.shape[1] < 640 or cropped.shape[0] < 480:
                cropped = CvHelper.resize(cropped, new_width=640, new_height=480)
            images.append(cropped)
        return images

    @staticmethod
    def save(img, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        if img is not None:
            try:
                tmp = ImageUtil.compress(img)#, max_w=200)
                tmp = CvHelper.bgr2rgb(tmp)
                filename = datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
                if tmp is not None:
                    d = path + "/" + filename + ".jpg"
                    CvHelper.write_mat(tmp, d)
                else:
                    print("Could not save none type")
            except Exception as e:
                pass

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
    def process_for_shape_detection(mat):
        tmp = mat.copy()
        # Resize image for faster processing
        resized = CvHelper.resize(tmp, 1080)
        grey = CvHelper.greyscale(resized)

        # Inverse the colours and make foreground pixels white and background black
        inv = CvHelper.inverse(grey)
        thresh = CvHelper.otsu_binary(inv)
        erosion = CvHelper.erode(thresh)

        # Resize image back to original size to keep ratio
        result = CvHelper.resize(erosion, mat.shape[1])
        return result

    @staticmethod
    def process_for_shape_detection_old(mat):
        tmp = mat.copy()
        resized = CvHelper.resize(tmp, new_width=int(mat.shape[1]/4), new_height=int(mat.shape[0]/4))
        grey = CvHelper.greyscale(resized)
        thresh = CvHelper.binarise(grey, 240)
        # Convert all white pixels to black
        grey[thresh == 255] = 0
        # Remove noise
        erosion = CvHelper.erode(grey)
        dilate = CvHelper.dilate(erosion)
        thresh = CvHelper.adaptive_thresholding(dilate)
        result = CvHelper.resize(thresh, new_width=mat.shape[1], new_height=mat.shape[0])
        return result

    @staticmethod
    def process_for_shape_detection_bright_backlight(image):
        img = CvHelper.get_umat(image.copy())
        greyscale = CvHelper.greyscale(img)
        bright = CvHelper.adjust_gamma(greyscale, 2.5)
        blur = CvHelper.gaussian_blur(bright, kernel_size=5)
        thresh = CvHelper.get_mat(CvHelper.otsu_binary(blur))
        return thresh

    @staticmethod
    def process_shape_new(image):
        tmp = image.copy()
        resize = CvHelper.resize(tmp, new_width=int(image.shape[1]/2), new_height=int(image.shape[0]/2))
        grey = CvHelper.greyscale(resize)
        equ = CvHelper.equalise_hist(grey, by_tile=False, tile_size=20)
        lap = CvHelper.laplacian(equ)
        dilate = CvHelper.dilate(lap, 3, 1)
        morph = CvHelper.morph(dilate, CvEnums.MORPH_GRADIENT, CvEnums.K_ELLIPSE, kernel_size=3)
        thresh = CvHelper.otsu_binary(morph, 240)
        canny = CvHelper.canny_thresholding(thresh)
        resize = CvHelper.resize(canny, new_width=image.shape[1], new_height=image.shape[0] / 4)
        CvHelper.display("Process", resize)
        return resize

    @staticmethod
    def remove_shadows(frames):
        fgbg = CvHelper.create_background_subtractor_mog2()
        fgbg.setDetectShadows(True)

        shadowless = []
        for frame in frames:
            tmp = fgbg.apply(frame)

            #tmp[tmp == 127] = 0
            shadowless.append(fgbg.getBackgroundImage())

        out = None
        return shadowless, out

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
        inverse = CvHelper.inverse(mat)
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
    def char_roi(mat, rectangles):
        tmp = mat.copy()
        out_rectangles = []

        for rectangle in rectangles:
            potential_plate = ImageUtil.auto_crop(tmp, rectangle)
            umat = CvHelper.get_umat(potential_plate)
            greyscale = CvHelper.greyscale(umat)
            bright = CvHelper.adjust_gamma(greyscale, 2.0)
            dilate = CvHelper.dilate(bright, kernel_size=3, iterations=0)
            morph = CvHelper.morph(dilate, gradient_type=CvEnums.MORPH_OPEN, kernel_size=3,
                                   kernel_shape=CvEnums.K_ELLIPSE)
            otsu = CvHelper.get_mat(CvHelper.otsu_binary(morph, 240))
            contours, __ = ContourHandler.find_contours(otsu, ret_mode=CvEnums.RETR_LIST,
                                                        approx_method=CvEnums.CHAIN_APPROX_NONE)
            if len(contours) > 0:
                r, boxs = ContourHandler.get_characters_roi(contours, potential_plate)
                if 2 <= len(r) <= 10:
                    out_rectangles.append(rectangle)

        return out_rectangles

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