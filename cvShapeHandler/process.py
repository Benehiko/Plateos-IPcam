from cvShapeHandler.imageprocessing import ImagePreProcessing
from cvShapeHandler.shapehandler import ShapeHandler
from cvShapeHandler.imagedraw import ImageDraw
from cvShapeHandler.imagedisplay import ImageDisplay
from cvShapeHandler.numpyencoder import NumpyEncoder


import logging
import json


class Process:

    def __init__(self, resize=False, draw_enable=False, show_image=False):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Captured image is rgb, convert to bgr
        #self.img = img  # ImagePreProcessing.rgb2bgr(img)
        self.imgShapeH = None
        self.draw_enable = draw_enable
        self.show_image = show_image
        self.resize = resize

    def process_for_tess(self, image, rectangles):
        images = []
        for rectangle in rectangles:
            crop_img = ImagePreProcessing.auto_crop(image.copy(), rectangle)
            crop_img = ImagePreProcessing.togray(crop_img)
            crop_img = ImagePreProcessing.equaHist(crop_img)
            crop_img = ImagePreProcessing.morph(crop_img, "close")
            crop_img = ImagePreProcessing.denoise(crop_img)
            images.append(crop_img)
        return images

    def process(self, image):
        # Resize image
        img = image.copy()

        self.imgShapeH = ShapeHandler(img)
        contours = self.imgShapeH.findcontours()
        if len(contours) > 0:

            rectangles, box_rectangles = self.imgShapeH.getRectangles(contours)

            if len(rectangles) > 0:
                if self.draw_enable:
                    try:
                        img = ImageDraw.draw(img, box_rectangles, "Green", 5)
                    except Exception as e:
                        self.logger.error(e)

                print("Image has rectangles!")
                return img, rectangles

        return None, None

    def rectangle2json(self, rectangles):
        inner = {'rectangles': {}}
        counter = 0
        for rectangle in rectangles:
            inner['rectangles'][counter] = NumpyEncoder().default(rectangle)
            counter += 1

        j = json.dumps(inner)
        return j

    def overlay_handler(self, rectangles):
        h, w, c = self.img.shape
        layer1 = Process.create_transparent_img(size=(h, w))  # opencv height then width
        res = layer1[:]
        layer2 = ImageDraw.draw(res, rectangles, "Green", 10)
        cnd = layer2[:, :, 3] > 0
        res[cnd] = layer2[cnd]
        res = ImagePreProcessing.cv_resize_compress(res, max_w=1280, max_h=960)
        height, width, channels = res.shape
        b = ImagePreProcessing.convert_img2bytes(res)
        # self.capture_handler.add_overlay(img_bytes=b, size=(width, height))

    @staticmethod
    def save(path, image=None):
        try:
            if image is not None:
                ImagePreProcessing.save(image, path)
            else:
                print("Image is none")#ImagePreProcessing.save(self.img, path)
        except Exception as e:
            logging.error(e)

    @staticmethod
    def compress(image):
        try:
            if image is not None:
                return ImagePreProcessing.cv_resize_compress(image)
            else:
                return None
        except Exception as e:
            logging.error(e)

    @staticmethod
    def normalise_image(image):
        try:
            if image is not None:
                return ImagePreProcessing.bgr2rgb(image)
            else:
                return None
        except Exception as e:
            logging.error(e)

    @staticmethod
    def rgb2bgr(image):
        try:
            if image is not None:
                return ImagePreProcessing.rgb2bgr(image)
        except Exception as e:
            logging.error(e)
    @staticmethod
    def create_transparent_img(size=(960, 1280)):
        return ImagePreProcessing.create_img(size=size)  # Opencv prefers Height and then Width thus (h,w)
