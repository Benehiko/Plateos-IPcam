from tesserocr import PyTessBaseAPI, PSM, OEM
from cvShapeHandler.imageprocessing import ImagePreProcessing
from numberplate.Numberplate import Numberplate
from PIL import Image
import os
import numpy as np


class Tess:
    def __init__(self):
        ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
        os.environ["TESSDATA_PREFIX"] = ROOT_DIR + "/tessdata"
        self.t = PyTessBaseAPI(psm=PSM.SINGLE_LINE, oem=OEM.TESSERACT_LSTM_COMBINED, lang='eng')
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

    def process(self, images, camera):
        extract = []
        for image in images:
            if image is not None:
                #image = ImagePreProcessing.bgr2rgb(image)
                tmp = Image.fromarray(np.uint8(image))
                #image.tile = [e for e in image.tile if e[1][2] < 2181 and e[1][3] < 1294]
                # image.show()
                self.t.SetImage(tmp)
                #print(self.t.AllWordConfidences())
                text = self.t.GetUTF8Text().replace("\n","")
                text = text.replace(" ","")
                if self.numberplate.isPlate(text):
                    extract.append(text)
                    camera.callback(image)
        return extract

    def download(self):
        pass
