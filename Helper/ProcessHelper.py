import asyncio

from cvlib.ContourHandler import ContourHandler
from cvlib.CvEnums import CvEnums
from cvlib.CvHelper import CvHelper
from cvlib.ImageUtil import ImageUtil
import multiprocessing as mp


class ProcessHelper:

    @staticmethod
    def analyse_frames(frame):
        if frame is not None:
            results = ProcessHelper.get_numberplate(frame)
            results = [x for x in results if x is not None]
            return results
        return None

    @staticmethod
    def get_numberplate(frame):
        tmp = frame.copy()
        results = None
        f = ImageUtil.process_for_shape_detection_bright_backlight(tmp)
        contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST)
        height, width, __ = tmp.shape
        rectangles, boxes, angles = ContourHandler.get_rectangles(contours, mat_width=width, mat_height=height,
                                                                  area_bounds=(0.02, 0.5),
                                                                  min_point=(0.2, 0.2), max_point=(5, 5))

        if len(rectangles) > 0:
            # drawn = CvHelper.draw_boxes(frame, boxes, CvEnums.COLOUR_GREEN, 5)

            pool = mp.Pool(processes=len(rectangles))
            output = [pool.apply_async(ImageUtil.char_roi, args=(tmp, r)) for r in rectangles]
            results = [o.get() for o in output]
            potential_plates = [item[0] for item in results if len(item) > 0]
            pool.close()
            pool.join()

            # CvHelper.display("Drawn", drawn, size=(640, 480))

            if len(potential_plates) > 0:
                pool = mp.Pool(processes=len(potential_plates))
                out = [pool.apply_async(ImageUtil.process_for_tess, args=(tmp, p)) for p in potential_plates]
                results = [p.get() for p in out]
                results = [item for item in results if len(item) > 0]
                pool.close()
                pool.join()

        return results
