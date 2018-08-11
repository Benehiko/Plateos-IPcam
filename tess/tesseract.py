from tesserocr import PyTessBaseAPI, PSM, OEM
from numberplate.Numberplate import Numberplate
from PIL import Image

import os
import numpy as np


class Tess:

    def __init__(self, backdrop):
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        os.environ["TESSDATA_PREFIX"] = ROOT_DIR + "/tessdata"
        self.t = PyTessBaseAPI(psm=PSM.SINGLE_BLOCK, oem=OEM.TESSERACT_LSTM_COMBINED, lang='eng')
        self.t.SetVariable("load_system_dawg", "false")
        self.t.SetVariable("load_freq_dawg", "false")
        self.t.SetVariable("load_punc_dawg", "false")
        self.t.SetVariable("load_number_dawg", "false")
        self.t.SetVariable("load_unambig_dawg", "false")
        self.t.SetVariable("load_bigram_dawg", "false")
        self.t.SetVariable("load_fixed_length_dawgs", "false")
        self.t.SetVariable("tessedit_create_hocr", "0")
        self.t.SetVariable("tessedit_char_whitelist", "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

        self.backdrop = backdrop

    def process(self, image):
        if image is not None:
            tmp = Image.fromarray(np.uint8(image))
            self.t.SetImage(tmp)
            text = Numberplate.sanitise(self.t.GetUTF8Text())
            #print("Raw Output:", text)
            plate_type, confidence = Numberplate.validate(text, use_provinces=True)
            if len(plate_type) > 0 and confidence > 0:
                self.backdrop.callback_tess((text, plate_type, confidence, image))

    def process_with_roi(self, image, rectangles):
        chars = []

        if image is not None:
            tmp = Image.fromarray(np.uint8(image))
            self.t.SetImage(tmp)
            for roi in rectangles:
                #print(roi)
                ((x1, y1), (x2, y2), _) = roi
                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)
                self.t.SetRectangle(x1, y1, x2, y2)
                chars.append(Numberplate.sanitise(self.t.GetUTF8Text()))
            print(chars)

            text = ''.join(chars)
            if Numberplate.validate(text):
                self.backdrop.callback_tess((text, image))


    def download(self):
        pass

