import asyncio

import cv2

from Handlers.PropertyHandler import PropertyHandler
from cvlib.ContourHandler import ContourHandler
from cvlib.CvEnums import CvEnums
from cvlib.CvHelper import CvHelper
from cvlib.ImageUtil import ImageUtil


class ProcessHelper:

    # TODO: Add type mapping and return types to methods with correct descriptions
    def __init__(self, cv_q):
        self.cv_q = cv_q
        self.propertyHandler = PropertyHandler()

    def analyse_frames(self, frame):
        width, height, __ = frame.shape
        frame = frame[0 + int(0.1 * height):-int(0.15 * height), :]

        if frame is not None:
            results, drawn, raw, chars = self.get_numberplate(frame)
            if results is not None:
                results = [x for x in results if x is not None]
                return results, drawn, raw, chars
            return results, drawn, raw, chars
        return None, None, None, None

    def get_numberplate(self, frame):
        drawn = frame.copy()
        results = None
        raw = None
        chars = None

        try:
            self.propertyHandler.get_cv_settings(self.cv_q)
            settings = self.propertyHandler.cv_settings
            while not self.cv_q.empty():
                settings = self.cv_q.get()

                # if len(settings) == 0:
                #     settings = PropertyHandler.cv_settings

            area_bounds = (float(settings["shape"]["area"]["min"]), float(settings["shape"]["area"]["max"]))
            min_point = (float(settings["shape"]["width"]["min"]), float(settings["shape"]["height"]["min"]))
            max_point = (float(settings["shape"]["width"]["max"]), float(settings["shape"]["height"]["max"]))
            char_bounds = (float(settings["char"]["area"]["min"]), float(settings["char"]["area"]["max"]))
            char_min = (float(settings["char"]["width"]["min"]), float(settings["char"]["height"]["min"]))
            char_max = (float(settings["char"]["width"]["max"]), float(settings["char"]["height"]["max"]))

            tmp = frame.copy()

            f = ImageUtil.process_for_shape_detection_bright_backlight(tmp, settings)
            raw = f
            contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST,
                                                        approx_method=CvEnums.CHAIN_APPROX_NONE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:]
            height, width, __ = tmp.shape
            rectangles, boxes, angles = ContourHandler().get_rectangles(contours, settings, mat_width=width,
                                                                        mat_height=height,
                                                                        area_bounds=area_bounds,
                                                                        min_point=min_point, max_point=max_point)

            if len(rectangles) > 0:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                pool = []
                for r in rectangles:
                    pool.append(
                        asyncio.ensure_future(ImageUtil.char_roi(tmp, r, char_bounds, (char_min, char_max)),
                                              loop=loop))

                potential_plates = loop.run_until_complete(asyncio.gather(*pool))
                potential = [(item[0], item[2]) for item in potential_plates if item[0] is not None]
                drawn_chars = [item[1] for item in potential_plates if item[1] is not None]

                loop.close()

                drawn = CvHelper.draw_boxes(drawn, boxes, CvEnums.COLOUR_GREEN, 5)
                chars = drawn_chars
                # Potential is a list of Binarised (otsu) images
                if len(potential) > 0:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    pool = [asyncio.ensure_future(ImageUtil.process_for_tess(data=p), loop=loop)
                            for
                            p in
                            potential]
                    results = loop.run_until_complete(asyncio.gather(*pool))
                    loop.close()

        except Exception as e:
            print(e)
            pass

        return results, drawn, raw, chars
