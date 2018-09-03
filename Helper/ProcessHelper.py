import asyncio
import datetime
import time

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
            # #shadowless, mat_background = ImageUtil.remove_shadows(frames)
            # now = datetime.datetime.now()
            # if len(historic_array) == 0:
            #     historic_array.append((frames[0].copy(), now))
            # else:
            #     diff = now - historic_array[0][1]
            #     if datetime.timedelta(seconds=2) < diff:
            #         del historic_array[0]
            #         historic_array.append((frames[0].copy(), now))

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
        # obj_roi = ImageUtil.process_change(historic_frames, frame)
        #
        # if len(obj_roi) > 0:
        #     targets = ImageUtil.get_sub_images(frame, obj_roi)
        #
        #     for target in targets:
        tmp = frame.copy()
        f = ImageUtil.process_shape_new(tmp)
        contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST)
        rectangles, boxes, angles = ContourHandler.get_rectangles(contours, tmp, area_bounds=(0.025, 5),
                                                                  min_point=(1, 1), max_point=(10, 10))
        if len(rectangles) > 0:
            drawn = CvHelper.draw_boxes(frame, boxes, colour=CvEnums.COLOUR_GREEN, thickness=5)
            CvHelper.display("Drawn", drawn)
            potential_plates = ImageUtil.char_roi(tmp, rectangles)
            if potential_plates is not None:
                print(len(potential_plates))
                cropped_array = ImageUtil.process_for_tess(image=tmp, rectangles=potential_plates)
                return cropped_array

        return None
