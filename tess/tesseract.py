import asyncio
from datetime import datetime
from io import BytesIO
from tesserocr import PyTessBaseAPI, PSM, OEM

import numpy as np
from PIL import Image

from Handlers.NumberplateHandler import NumberplateHandler
from cvlib.ImageUtil import ImageUtil


class Tess:

    def __init__(self):
        # noinspection PyArgumentList,PyArgumentList
        self.t = PyTessBaseAPI(psm=PSM.SINGLE_BLOCK, oem=OEM.LSTM_ONLY, lang="eng")
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


    async def runner(self, data):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ms = datetime.now().strftime('%Y-%m-%d %H:%M:%S:%f')
        plate = {"image": data[0], "char-len": data[1], "time": ms}
        if data is not None:
            image = Image.fromarray(np.uint8(data[0]))
            temp = BytesIO()
            image.save(temp, "JPEG", dpi=(600, 400))
            temp.seek(0)
            image = Image.open(temp)
            self.t.SetImage(image)
            raw_text = self.t.GetUTF8Text()
            if len(raw_text) > 0:
                text = NumberplateHandler.sanitise(raw_text)
                word_conf = self.t.MapWordConfidences()
                tess_confidence = 2
                if len(word_conf) > 0:
                    for x in word_conf:
                        if text == x[0]:
                            tess_confidence = x[1]
                            break

                p_data = NumberplateHandler.validate(text)
                if p_data[0] is not None:
                    country, province, confidence = p_data
                    image = ImageUtil.compress(data[0], max_w=200)
                    confidence = confidence + round(float((tess_confidence / 100) / 2), 2)
                    # plate = {"plate": text, "country": country, "province": province, "confidence": confidence,
                    # "image": image, "time": now, "char-len": data[1]}
                    plate = [("plate", text), ("country", country), ("province", province), ("confidence", confidence),
                             ("image", image), ("time", now), ("char-len", data[1])]
                    print("Plate:", text, "Country:", country, "Province:", province, "Confidence:", confidence,
                          "Time:", now)
                return dict(plate)

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
