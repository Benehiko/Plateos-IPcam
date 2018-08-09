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

        self.numberplate = Numberplate()
        self.backdrop = backdrop

    def process(self, image):
        if image is not None:
            tmp = Image.fromarray(np.uint8(image))
            self.t.SetImage(tmp)
            text = self.numberplate.sanitise(self.t.GetUTF8Text())

            if self.numberplate.isPlate(text):
                self.backdrop.callbackPlate((text, image))


    def download(self):
        pass

