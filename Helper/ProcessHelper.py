import asyncio
import cv2

from DataHandler.PropertyHandler import PropertyHandler
from cvlib.ContourHandler import ContourHandler
from cvlib.CvEnums import CvEnums
from cvlib.CvHelper import CvHelper
from cvlib.ImageUtil import ImageUtil


class ProcessHelper:

    @staticmethod
    def analyse_frames(frame):
        if frame is not None:
            results = ProcessHelper.get_numberplate(frame)
            if results is not None:
                results = [x for x in results if x is not None]
                return results
        return None

    @staticmethod
    def get_numberplate(frame):
        tmp = frame.copy()

        results = None
        try:
            settings = PropertyHandler.cv_settings
            area_bounds = (float(settings["shape"]["area"]["min"]), float(settings["shape"]["area"]["max"]))
            min_point = (float(settings["shape"]["width"]["min"]), float(settings["shape"]["height"]["min"]))
            max_point = (float(settings["shape"]["width"]["max"]), float(settings["shape"]["height"]["max"]))
            char_bounds = (float(settings["char"]["area"]["min"]), float(settings["char"]["area"]["max"]))
            char_min = (float(settings["char"]["width"]["min"]), float(settings["char"]["height"]["min"]))
            char_max = (float(settings["char"]["width"]["max"]), float(settings["char"]["height"]["max"]))

            f = ImageUtil.process_for_shape_detection_bright_backlight(tmp)
            contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST,
                                                        approx_method=CvEnums.CHAIN_APPROX_NONE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:]
            height, width, __ = tmp.shape
            rectangles, boxes, angles = ContourHandler().get_rectangles(contours, mat_width=width, mat_height=height,
                                                                        area_bounds=area_bounds,
                                                                        min_point=min_point, max_point=max_point)

            if len(rectangles) > 0:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                pool = []
                for r in rectangles:
                    pool.append(
                        asyncio.ensure_future(ImageUtil.char_roi(tmp, r, char_bounds, (char_min, char_max)), loop=loop))

                potential_plates = loop.run_until_complete(asyncio.gather(*pool))
                potential_plates = [item for item in potential_plates if item is not None]
                loop.close()

                # display = CvHelper.draw_boxes(tmp.copy(), boxes, CvEnums.COLOUR_GREEN, 5)
                # CvHelper.display("Drawn", display, size=(640, 480))
                if len(potential_plates) > 0:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    pool = [asyncio.ensure_future(ImageUtil.process_for_tess(data=p), loop=loop) for p in
                            potential_plates]
                    results = loop.run_until_complete(asyncio.gather(*pool))
                    loop.close()
        except Exception as e:
            print(e)
            pass

        return results
