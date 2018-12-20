import asyncio
from datetime import datetime, timedelta
from tesserocr import PyTessBaseAPI, PSM, OEM

import numpy as np
from PIL import Image
from io import BytesIO
from cvlib.ImageUtil import ImageUtil
from numberplate.Numberplate import Numberplate


class Tess:

    def __init__(self, backdrop):
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
        self.backdrop = backdrop
        self.cached = []
        self.then = datetime.now()

    async def runner(self, nparray):
        if nparray is not None:
            if not isinstance(nparray, list):
                image = Image.fromarray(np.uint8(nparray))
                temp = BytesIO()
                image.save(temp, "JPEG", dpi=(600, 400))
                temp.seek(0)
                image = Image.open(temp)
                self.t.SetImage(image)
                raw_text = self.t.GetUTF8Text()
                tess_confidence = self.t.MeanTextConf()
                # if tess_confidence >= 30:  # any(item >= 70 for item in tess_confidence):
                text = Numberplate.sanitise(raw_text)
                plate_type, confidence = Numberplate.validate(text, use_provinces=True)
                if plate_type is not None and confidence > 0:
                    image = ImageUtil.compress(nparray, max_w=200)
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    plate = (text, plate_type, confidence + ((tess_confidence / 100) / 2), now, image)
                    self.backdrop.callback_tess(plate)
                    return plate
            else:
                print("It's a list", nparray)
        return None

    def multi(self, images):
        try:
            if images is not None:
                if len(images) > 0:
                    event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(event_loop)
                    pool = [asyncio.ensure_future(self.runner(i)) for i in images]
                    results = event_loop.run_until_complete(asyncio.gather(*pool))
                    results = [x for x in results if x is not None]
                    event_loop.close()
                    if len(results) > 0:
                        self.cached = self.cached + results

                    now = datetime.now()
                    diff = now - self.then
                    if timedelta(minutes=1) < diff:
                        if len(self.cached) > 0:
                            self.backdrop.cache(self.cached)
                            self.cached = []
                            self.then = now
        except Exception as e:
            print(e)
            pass
