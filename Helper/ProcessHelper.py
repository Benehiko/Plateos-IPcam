import asyncio
import cv2

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
        f = ImageUtil.process_for_shape_detection_bright_backlight(tmp)
        contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_EXTERNAL, approx_method=CvEnums.CHAIN_APPROX_NONE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:]
        height, width, __ = tmp.shape
        rectangles, boxes, angles = ContourHandler().get_rectangles(contours, mat_width=width, mat_height=height,
                                                                    area_bounds=(0.028, 0.45),
                                                                    min_point=(0.1, 0.1), max_point=(8, 4))

        if len(rectangles) > 0:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            pool = []
            for r in rectangles:
                pool.append(asyncio.ensure_future(ImageUtil.char_roi(tmp, r), loop=loop))

            potential_plates = loop.run_until_complete(asyncio.gather(*pool))
            potential_plates = [item for item in potential_plates if item is not None]
            loop.close()

            # display = CvHelper.draw_boxes(tmp.copy(), boxes, CvEnums.COLOUR_GREEN, 5)
            # CvHelper.display("Drawn", display, size=(640, 480))

            if len(potential_plates) > 0:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                pool = [asyncio.ensure_future(ImageUtil.process_for_tess(data=p), loop=loop) for p in potential_plates]
                results = loop.run_until_complete(asyncio.gather(*pool))
                loop.close()

        return results
