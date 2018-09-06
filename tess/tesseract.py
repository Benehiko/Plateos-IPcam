import asyncio
import locale

from datetime import datetime
from tesserocr import PyTessBaseAPI, PSM, OEM

import numpy as np
from PIL import Image

from cvlib.ImageUtil import ImageUtil
from numberplate.Numberplate import Numberplate


class Tess:

    def __init__(self, backdrop):
        locale.setlocale(locale.LC_ALL, "C")
        self.t = PyTessBaseAPI(psm=PSM.SINGLE_BLOCK, oem=OEM.TESSERACT_LSTM_COMBINED, lang='eng')
        #self.t.SetVariable("psm", "13")
        #self.t.SetVariable("oem", "2")
        self.t.SetVariable("load_system_dawg", "false")
        self.t.SetVariable("load_freq_dawg", "false")
        self.t.SetVariable("load_punc_dawg", "false")
        self.t.SetVariable("load_number_dawg", "false")
        self.t.SetVariable("load_unambig_dawg", "false")
        self.t.SetVariable("load_bigram_dawg", "false")
        self.t.SetVariable("load_fixed_length_dawgs", "false")
        self.t.SetVariable("tessedit_create_hocr", "1")
        self.t.SetVariable("textord_force_make_prop_words", "false")
        self.t.SetVariable("tessedit_char_whitelist", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
        self.backdrop = backdrop

    async def runner(self, image):
        tmp = Image.fromarray(np.uint8(image))
        self.t.SetImage(tmp)
        text = Numberplate.sanitise(self.t.GetUTF8Text())
        plate_type, confidence = Numberplate.validate(text, use_provinces=True)
        if plate_type is not None and confidence > 0:
            image = ImageUtil.compress(image, max_w=200)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            plate = ((text, plate_type, confidence, now, image))
            self.backdrop.callback_tess(plate)

    def multi(self, images):
        pool = []
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for image in images:
            if image is not None:
                pool.append(asyncio.ensure_future(self.runner(image), loop=loop))

        loop.run_until_complete(asyncio.gather(*pool))
        loop.close()

    def process(self, image):
        if image is not None:
            tmp = Image.fromarray(np.uint8(image))
            self.t.SetImage(tmp)
            text = Numberplate.sanitise(self.t.GetUTF8Text())
            plate_type, confidence = Numberplate.validate(text, use_provinces=True)
            if plate_type is not None and confidence > 0:
                image = ImageUtil.compress(image, max_w=200)
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.backdrop.callback_tess((text, plate_type, confidence, now, image))

    def process_with_roi(self, image, rectangles):
        chars = []

        if image is not None:
            tmp = Image.fromarray(np.uint8(image))
            self.t.SetImage(tmp)
            for roi in rectangles:
                ((x1, y1), (x2, y2), _) = roi
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
                self.t.SetRectangle(x1, y1, x2, y2)
                chars.append(Numberplate.sanitise(self.t.GetUTF8Text()))
            print(chars)

            text = ''.join(chars)
            result, confidence = Numberplate.validate(text, use_provinces=True)
            if result is not None:
                self.backdrop.callback_tess((text, image))

    def download(self):
        pass

