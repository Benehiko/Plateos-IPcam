import json
import logging

from cvShapeHandler.gpuhandler import GPUHandler
from cvShapeHandler.imagedisplay import ImageDisplay
from cvShapeHandler.imagedraw import ImageDraw
from cvShapeHandler.imageprocessing import ImagePreProcessing
from cvShapeHandler.numpyencoder import NumpyEncoder
from cvShapeHandler.shapehandler import ShapeHandler


class ImgProcess:

    def __init__(self, resize=False, draw_enable=False, show_image=False):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Captured image is rgb, convert to bgr
        #self.img = img  # ImagePreProcessing.rgb2bgr(img)
        self.imgShapeH = None
        self.draw_enable = draw_enable
        self.show_image = show_image
        self.resize = resize

    def highlight(self, image, regions):
        for rectangle in regions:
            centre, dimensions, theta = rectangle
            h, w = dimensions
            thresh = ImagePreProcessing.otsu_binary(image[h:w], 240)
            image[thresh == 0] = (0, 0, 255)

        ImageDisplay.display(image, "Highlight")
        return image

    def process_for_tess(self, image, rectangles):
        images = []
        for rectangle in rectangles:
            cropped = ImagePreProcessing.auto_crop(image.copy(), rectangle)
            gray = ImagePreProcessing.togray(cropped)
            ugray = GPUHandler.toUmat(gray)
            inverse = ImagePreProcessing.inverse(ugray)
            thresh = ImagePreProcessing.otsu_binary(inverse)
            compare = GPUHandler.getMat(thresh)
            deskew = ImagePreProcessing.deskew(gray, compare)
            images.append(deskew)
        return images

    def char_roi(self, cropped):
        img = cropped.copy()
        self.imgShapeH = ShapeHandler(img)
        contours, binary = self.imgShapeH.findcontours()
        if len(contours) > 0:
            rectangles, box_rectangles = self.imgShapeH.getCharacters(contours)

            if len(rectangles) > 0:
                if self.draw_enable:
                    try:
                        img = ImageDraw.draw(img, box_rectangles, "Green", 5)
                    except Exception as e:
                        self.logger.error(e)
                    #Process.save("drawn", img)
                    #ImageDisplay.display(binary, "Drawn Display")
                return img, rectangles

        return None, None

    def process(self, image):
        if image is not None:
            corrected = image.copy()

            self.imgShapeH = ShapeHandler(corrected)
            contours = self.imgShapeH.findcontours()

            if len(contours) > 0:
                rectangles, box_corrected, angles = self.imgShapeH.getRectangles(contours)
                if len(rectangles) > 0:
                    corrected = ImageDraw.draw(corrected, box_corrected, "Red", 10)
                    for a in angles:
                        corrected = ImageDraw.draw_text(corrected, str(a[0]), a[1], "Red", 3, 3)

                    return rectangles, corrected

            return None, corrected
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
        layer1 = ImgProcess.create_transparent_img(size=(h, w))  # opencv height then width
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
