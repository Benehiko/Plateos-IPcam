import asyncio

from cvlib.ContourHandler import ContourHandler
from cvlib.CvEnums import CvEnums
from cvlib.CvHelper import CvHelper
from cvlib.ImageUtil import ImageUtil


class ProcessHelper:

    @staticmethod
    def analyse_frames(frames):
        if len(frames) > 0:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            pool = []
            for frame in frames:
                pool.append(asyncio.ensure_future(ProcessHelper.get_numberplate(frame), loop=loop))

            results = loop.run_until_complete(asyncio.gather(*pool))
            results = [x for x in results if x is not None]

            out = []
            for r in results:
                out += r

            loop.close()
            return out

        return None

    @staticmethod
    @asyncio.coroutine
    def get_numberplate(frame):
        tmp = frame.copy()
        f = ImageUtil.process_for_shape_detection_bright_backlight(tmp)
        contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST)
        rectangles, boxes, angles = ContourHandler.get_rectangles(contours, tmp, area_bounds=(0.02, 2),
                                                                  min_point=(0.2, 0.2), max_point=(10, 10))
        if len(rectangles) > 0:
            #drawn = CvHelper.draw_boxes(frame, boxes, colour=CvEnums.COLOUR_GREEN, thickness=5)
            #CvHelper.display("Drawn", drawn)
            potential_plates = ImageUtil.char_roi(tmp, rectangles)
            if len(potential_plates) > 0:
                cropped_array = ImageUtil.process_for_tess(image=tmp, rectangles=potential_plates)
                return cropped_array

        return None
