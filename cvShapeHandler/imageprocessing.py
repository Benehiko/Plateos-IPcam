import cv2, imutils, math
import datetime, pathlib
import numpy as np
import logging

from cvShapeHandler.gpuhandler import GPUHandler
from cvShapeHandler.imagedisplay import ImageDisplay


class ImagePreProcessing:

    def __init__(self):
        pass
        # cv2.ocl.setUseOpenCL(False)

    @staticmethod
    def deskew(image, thresh):
        # grab the (x, y) coordinates of all pixel values that
        # are greater than zero, then use these coordinates to
        # compute a rotated bounding box that contains all
        # coordinates
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]

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
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated

    @staticmethod
    def rotate_image(img, angle):
        height, width = img.shape[:2]
        image_center = (width / 2, height / 2)

        rotation_mat = cv2.getRotationMatrix2D(image_center, angle, 1)

        radians = math.radians(angle)
        sin = math.sin(radians)
        cos = math.cos(radians)
        bound_w = int((height * abs(sin)) + (width * abs(cos)))
        bound_h = int((height * abs(cos)) + (width * abs(sin)))

        rotation_mat[0, 2] += ((bound_w / 2) - image_center[0])
        rotation_mat[1, 2] += ((bound_h / 2) - image_center[1])

        rotated_mat = cv2.warpAffine(img, rotation_mat, (bound_w, bound_h))
        return rotated_mat

    @staticmethod
    def sub_image(image, center, theta, width, height):
        """Extract a rectangle from the source image.

        	image - source image
        	center - (x,y) tuple for the centre point.
        	theta - angle of rectangle.
        	width, height - rectangle dimensions.
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

        return cv2.warpAffine(image, mapping, (width, height), flags=cv2.WARP_INVERSE_MAP,
                              borderMode=cv2.BORDER_REPLICATE)

    @staticmethod
    def crop_minAreaRect(img, rect):
        ((x, y), (w, h), angle) = rect
        # x = int(x)
        # y = int(y)
        # w = int(w)
        # h = int(h)
        img_crop = ImagePreProcessing.crop(img, (x, y, w, h))
        # img_crop = ImagePreProcessing.rotate_image(img_crop, -180)
        # img_crop = img[y:h, x:w]
        return img_crop

    @staticmethod
    def auto_crop(image_source, rectangle):
        """Return a rotated and cropped version of the source image"""

        # First slightly crop edge - some images had a rogue 2 pixel black edge on one side
        init_crop = 10
        h, w = image_source.shape[:2]
        image_source = image_source[init_crop:init_crop + (h - init_crop * 2), init_crop:init_crop + (w - init_crop * 2)]
        # Add back a white border
        image_source = cv2.copyMakeBorder(image_source, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        centre, dimensions, theta = rectangle

        width = int(dimensions[0])
        height = int(dimensions[1])

        box = cv2.boxPoints(rectangle)
        box = np.int0(box)

        M = cv2.moments(box)
        cx = int(M['m10'] / M['m00'])
        cy = int(M['m01'] / M['m00'])

        image_patch = ImagePreProcessing.sub_image(image_source, (cx, cy), theta + 90, height, width)


        return image_patch

    @staticmethod
    def crop(img, bbox):
        x1, y1, x2, y2 = bbox
        if x1 < 0 or y1 < 0 or x2 > img.shape[1] or y2 > img.shape[0]:
            img, x1, x2, y1, y2 = ImagePreProcessing.pad_img_to_fit_bbox(img, x1, x2, y1, y2)
        return img[y1:y2, x1:x2, :]

    @staticmethod
    def pad_img_to_fit_bbox(img, x1, x2, y1, y2):
        img = np.pad(img, ((np.abs(np.minimum(0, y1)), np.maximum(y2 - img.shape[0], 0)),
                           (np.abs(np.minimum(0, x1)), np.maximum(x2 - img.shape[1], 0)), (0, 0)), mode="constant")
        y1 += np.abs(np.minimum(0, y1))
        y2 += np.abs(np.minimum(0, y1))
        x1 += np.abs(np.minimum(0, x1))
        x2 += np.abs(np.minimum(0, x1))
        return img, x1, x2, y1, y2

    @staticmethod
    def erode(img):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        erosion = cv2.erode(img, kernel, iterations=1)
        return erosion

    @staticmethod
    def morph(img):
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        morph = cv2.morphologyEx(img, cv2.MORPH_CLOSE, kernel)
        return morph

    @staticmethod
    def equaHist(img):
        # The code commented below only equalises the whole image and not piece by piece. This creates noise.
        # equ = cv2.equalizeHist(img)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(15, 15))
        result = clahe.apply(img)
        return result

    @staticmethod
    def binary(img, thresh=127):
        ret, img_bin = cv2.threshold(img, thresh, 255, 0)
        return img_bin

    @staticmethod
    def otsu_binary(img, thresh=0):
        # blur = cv2.GaussianBlur(img, (5, 5), 0)
        thresh = cv2.threshold(img, thresh, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        return thresh

    @staticmethod
    def dilate(img):
        kernel = np.ones((5, 5), np.uint8)
        dilate = cv2.dilate(img, kernel, iterations=1)
        return dilate

    @staticmethod
    def togray(img):
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img_gray

    @staticmethod
    def get_histogram(img):
        return cv2.calcHist([img], [0], None, [256], [0, 256])

    @staticmethod
    def adaptiveBinnary(img):
        t = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        return t

    @staticmethod
    def tocanny(img, low_threshold):
        high_threshold = low_threshold * 3
        img_canny = cv2.Canny(img, low_threshold, high_threshold)
        return img_canny

    @staticmethod
    def denoise(img, intensity=2, search_window=21, block_size=7):
        denoise = cv2.fastNlMeansDenoising(img, intensity, search_window, block_size)
        # Usually searchWindows is 21 and blockSize is 7
        return denoise

    @staticmethod
    def blur(img, kernel_size=5, sigMaxX=0, sigMaxY=0):
        ksize = (kernel_size, kernel_size)
        blur = cv2.GaussianBlur(img, ksize, sigMaxX, sigMaxY)
        return blur

    @staticmethod
    def resize(img, newwidth):
        resized = imutils.resize(img, width=newwidth)
        return resized

    @staticmethod
    def cv_resize_compress(img, max_w=1640, max_h=1232, quality=65):
        try:
            # print("DEBUG: resize the image...using shape")
            img_h = img.shape[0]
            img_w = img.shape[1]
            new_h = img_h
            new_w = img_w

            # print("Image current resolution: ", str(img_w), "x", str(img_h))
            if img_w > max_w:
                new_w = max_w
                new_h = int((new_w * img_h) / img_w)

            if img_h > max_h:
                new_h = max_h

                new_w = int((new_h * img_w) / img_h)

            dist_size = (new_w, new_h)
            # print("New size:", str(dist_size))
            resized = cv2.resize(img, dist_size, interpolation=cv2.INTER_AREA)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]

            retval, buf = cv2.imencode('.jpg', resized, encode_param)
            return cv2.imdecode(buf, 1)  # Flag 1 since it's colour

        except Exception as e:
            logging.error(e)
            return None

    @staticmethod
    def create_img(size):
        img = np.zeros((size[0], size[1], 4), np.uint8)
        return img

    @staticmethod
    def convert_img2bytes(img):
        bytes = cv2.imencode('.jpg', img)[1].tostring()
        return bytes

    @staticmethod
    def save(img, path):
        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        if img is not None:
            # print("Saving image of", img.nbytes/10000000, "MB")
            try:
                tmp = ImagePreProcessing.cv_resize_compress(img, max_w=200)
                tmp = ImagePreProcessing.bgr2rgb(tmp)
                filename = datetime.datetime.now().strftime("%Y-%m-%d-%H_%M_%S")
                if tmp is not None:
                    d = path + "/" + filename + ".jpg"
                    cv2.imwrite(d, tmp)
                else:
                    print("Could not save none type")
            except Exception as e:
                logging.error(e)

    @staticmethod
    def rgb2bgr(img):
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    @staticmethod
    def bgr2rgb(img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return img

    @staticmethod
    def init_UMAT(img):
        return cv2.UMat(img.copy())

    @staticmethod
    def inverse(image):
        return cv2.bitwise_not(image)

    @staticmethod
    def process_for_shape_detection(image):
        img = image.copy()
        # Resize image for faster processing
        img_resize = ImagePreProcessing.resize(img, 1080)
        img_gray = ImagePreProcessing.togray(img_resize)

        # Inverse the colours and make foreground pixels white and background black
        inv = ImagePreProcessing.inverse(img_gray)
        thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        erosion = ImagePreProcessing.erode(thresh)
        # img_dilate = ImagePreProcessing.dilate(img_erosion)
        # img_denoise =  ImagePreProcessing.denoise(thresh)
        # thresh = ImagePreProcessing.adaptiveBinnary(img_erosion)

        # Resize image back to original size to keep ratio
        result = ImagePreProcessing.resize(erosion, image.shape[1])
        return result

    @staticmethod
    def process_for_shape_detection_bright_backlight(image):
        img = image.copy()
        # Resize image for faster processing
        img_resize = GPUHandler.toUmat(ImagePreProcessing.resize(img, int(image.shape[1]/4)))  # 1080
        img_gray = ImagePreProcessing.togray(img_resize)
        thresh = ImagePreProcessing.otsu_binary(img_gray, 240)
        # img_gray[thresh == 255] = 0
        # erode = ImagePreProcessing.erode(thresh)
        # dilate = ImagePreProcessing.dilate(erode)
        inv = ImagePreProcessing.inverse(thresh)
        #binary = ImagePreProcessing.adaptiveBinnary(inv)
        denoise = ImagePreProcessing.denoise(inv, intensity=5)

        # Resize image back to original size to keep ratio

        result = GPUHandler.getMat(denoise)
        #ImageDisplay.display("Processed", result)
        result = ImagePreProcessing.resize(result, image.shape[1])
        return result

    @staticmethod
    def process_for_shape_detection_old(image):
        img = image.copy()
        img_resize = ImagePreProcessing.resize(img, 1080)
        img_gray = ImagePreProcessing.togray(img_resize)
        img_thresh = ImagePreProcessing.binary(img_gray, 240)

        # Convert all white pixels to black
        img_gray[img_thresh == 255] = 0

        # Remove noise
        img_erosion = ImagePreProcessing.erode(img_gray)
        img_dilate = ImagePreProcessing.dilate(img_erosion)
        img_thresh = ImagePreProcessing.adaptiveBinnary(img_dilate)

        result = ImagePreProcessing.resize(img_thresh, image.shape[1])
        return result
