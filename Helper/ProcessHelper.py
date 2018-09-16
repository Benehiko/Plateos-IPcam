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
    async def get_numberplate(frame):
        tmp = frame.copy()
        results = None
        f = ImageUtil.process_for_shape_detection_bright_backlight(tmp)
        contours, __ = ContourHandler.find_contours(f, ret_mode=CvEnums.RETR_LIST)
        height, width, __ = tmp.shape
        rectangles, boxes, angles = ContourHandler.get_rectangles(contours, mat_width=width, mat_height=height, area_bounds=(0.02, 0.5),
                                                                  min_point=(0.2, 0.2), max_point=(5, 5))

        if len(rectangles) > 0:

            loop = asyncio.get_event_loop()
            pool = []

            drawn = CvHelper.draw_boxes(frame, boxes, CvEnums.COLOUR_GREEN, 5)

            for r in rectangles:
                pool.append(asyncio.ensure_future(ImageUtil.char_roi(mat=tmp, rectangle=r), loop=loop))
                (x, y), __, angle = r
                x = int(x)
                y = int(y)
                drawn = CvHelper.draw_text(drawn, str(angle), (x, y), CvEnums.COLOUR_RED)

            CvHelper.display("Drawn", drawn)
            potential_plates = await asyncio.gather(*pool)
            potential_plates = [item[0] for item in potential_plates if len(item) > 0]

            if len(potential_plates) > 0:
                pool = []
                for p in potential_plates:
                    pool.append(asyncio.ensure_future(ImageUtil.process_for_tess(mat=tmp, data=p), loop=loop))

                results = await asyncio.gather(*pool)
                results = [item for item in results if len(item) > 0]
                for res in results:
                    ImageUtil.save(res, 'blanks')

        return results
