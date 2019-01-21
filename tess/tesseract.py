import asyncio
from datetime import datetime
from io import BytesIO
from tesserocr import PyTessBaseAPI, PSM, OEM

import numpy as np
from PIL import Image

from Handlers.NumberplateHandler import NumberplateHandler
from cvlib.ImageUtil import ImageUtil


class Tess:
    """
    https://github.com/tesseract-ocr/tesseract/wiki/ImproveQuality#binarisation
    Sparse_Text_OSD seems to be the most accurate, WHILE RAW_LINE and SINGLE_BLOCK seems to be the fastest (inaccurate).

    Don't use LSTM and Tesseract Original together. Only LSTM (Trained Model).

    What seems to work the best is to Morph Dilate with a dilation of size 2x2 and shape Rectangle on an otsu bin image.
    Padding is also necessary (https://groups.google.com/forum/?utm_medium=email&utm_source=footer#!msg/tesseract-ocr/v26a-RYPSOE/2Sppq61GBwAJ)
    Although it is said to remove boarders, still pad the text with 10px

    Upped the DPI to a 720p image
    """

    # TODO: Add type mapping and return types to methods with correct descriptions

    def __init__(self):
        # noinspection PyArgumentList,PyArgumentList
        self.t = PyTessBaseAPI(psm=PSM.SPARSE_TEXT_OSD, oem=OEM.LSTM_ONLY, lang="eng")
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
        print("Tess Version", self.t.Version())

    async def runner(self, data):
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ms = datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
            if data is not None:
                plate = {"image": data[0], "char-len": data[1], "time": ms}
                image = Image.fromarray(np.uint8(data[0]))
                temp = BytesIO()
                image.save(temp, "JPEG", dpi=(1280, 720))
                temp.seek(0)
                image = Image.open(temp)
                self.t.SetImage(image)
                raw_text = self.t.GetUTF8Text()
                if len(raw_text) > 0:
                    text = NumberplateHandler.sanitise(raw_text)
                    if len(text) > 0:
                        word_conf = self.t.MapWordConfidences()
                        tess_confidence = 0
                        if len(word_conf) > 0:
                            for x in word_conf:
                                if text == x[0]:
                                    tess_confidence = x[1]
                                    break

                        p_data = NumberplateHandler.validate(text)
                        if None not in p_data:
                            country, province, confidence = p_data
                            image = ImageUtil.compress(data[0], max_w=200)
                            confidence = confidence + round(float((tess_confidence / 100) / 2), 2)
                            plate = [("plate", text), ("country", country), ("province", province),
                                     ("confidence", confidence),
                                     ("image", image), ("time", now), ("char-len", data[1])]
                            print("Plate:", text, "Country:", country, "Province:", province, "Confidence:", confidence,
                                  "Time:", now)
                return dict(plate)
        except Exception as e:
            print("Tess runner error", "\n", e)
            pass
        return None

    def multi(self, images):
        out = None
        try:
            if images is not None:
                if len(images) > 0:
                    event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(event_loop)
                    pool = [asyncio.ensure_future(self.runner(i)) for i in images]
                    tmp = event_loop.run_until_complete(asyncio.gather(*pool))
                    out = [x for x in tmp if x is not None]
                    event_loop.close()
        except Exception as e:
            print("Tesseract Error", e)
            pass
        return out
