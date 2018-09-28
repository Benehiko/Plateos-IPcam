import multiprocessing as mp
from datetime import datetime
from tesserocr import PyTessBaseAPI, PSM, OEM

import numpy as np
from PIL import Image

from cvlib.ImageUtil import ImageUtil
from numberplate.Numberplate import Numberplate


class Tess:

    def __init__(self, backdrop):
        # noinspection PyArgumentList,PyArgumentList
        self.t = PyTessBaseAPI(psm=PSM.CIRCLE_WORD, oem=OEM.TESSERACT_LSTM_COMBINED)
        self.t.SetVariable("load_system_dawg", "false")
        self.t.SetVariable("load_freq_dawg", "false")
        self.t.SetVariable("load_punc_dawg", "false")
        self.t.SetVariable("load_number_dawg", "false")
        self.t.SetVariable("load_unambig_dawg", "false")
        self.t.SetVariable("load_bigram_dawg", "false")
        self.t.SetVariable("load_fixed_length_dawgs", "false")
        self.t.SetVariable("tessedit_create_hocr", "0")
        self.t.SetVariable("textord_force_make_prop_words", "false")
        self.t.SetVariable("tessedit_char_whitelist", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.backdrop = backdrop

    def runner(self, image):
        if image is not None:
            if not isinstance(image, list):
                tmp = Image.fromarray(np.uint8(image))
                self.t.SetImage(tmp)
                text = Numberplate.sanitise(self.t.GetUTF8Text())
                plate_type, confidence = Numberplate.validate(text, use_provinces=True)
                if plate_type is not None and confidence > 0:
                    image = ImageUtil.compress(image, max_w=200)
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    plate = (text, plate_type, confidence, now, image)
                    return plate
        return None

    def multi(self, images):
        if images is not None:
            if len(images) > 0:
                pool = mp.Pool(processes=len(images))
                out = [pool.apply_async(self.runner(i)) for i in images]
                if out is not None:
                    result = [o.get() for o in out]
                    result = [r for r in result if r is not None]
                    pool.close()
                    pool.join()
                    if len(result) > 0:
                        for r in result:
                            self.backdrop.callback_tess(r)

    # def process(self, image):
    #     if image is not None:
    #         tmp = Image.fromarray(np.uint8(image))
    #         self.t.SetImage(tmp)
    #         text = Numberplate.sanitise(self.t.GetUTF8Text())
    #         plate_type, confidence = Numberplate.validate(text, use_provinces=True)
    #         if plate_type is not None and confidence > 0:
    #             image = ImageUtil.compress(image, max_w=200)
    #             now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #             self.backdrop.callback_tess((text, plate_type, confidence, now, image))
    #
    # def process_with_roi(self, image, rectangles):
    #     chars = []
    #
    #     if image is not None:
    #         tmp = Image.fromarray(np.uint8(image))
    #         self.t.SetImage(tmp)
    #         for roi in rectangles:
    #             ((x1, y1), (x2, y2), _) = roi
    #             x1 = int(x1)
    #             y1 = int(y1)
    #             x2 = int(x2)
    #             y2 = int(y2)
    #             self.t.SetRectangle(x1, y1, x2, y2)
    #             chars.append(Numberplate.sanitise(self.t.GetUTF8Text()))
    #         print(chars)
    #
    #         text = ''.join(chars)
    #         result, confidence = Numberplate.validate(text, use_provinces=True)
    #         if result is not None:
    #             return (text, image) # self.backdrop.callback_tess((text, image))
    #
    # def download(self):
    #     pass
