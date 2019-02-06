import asyncio
import time
from datetime import datetime, timedelta

from Handlers.CacheHandler import CacheHandler
from Handlers.NumberplateHandler import NumberplateHandler


class CachedNumberplateHandler:

    @staticmethod
    async def combine_tmp_data() -> list or None:
        """
        Combine Temporary directory npz files data into single List of dictionaries
        dict: {
           "plate", "province", "confidence", "time", "camera"
        }

        :param cv_tmp:
        :return:
        """

        async def load(x):
            return await CacheHandler.load("tmp", x)

        try:
            files = CacheHandler.get_file_list("tmp")
            result = []
            tmp_data = []
            if len(files) > 0:
                event_loop = asyncio.get_event_loop()
                pool = []
                for x in files:
                    pool.append(asyncio.ensure_future(load(x), loop=event_loop))

                data = await asyncio.gather(*pool)
                data = [x for x in data if x is not None]
                if len(data) > 0:
                    for x in data:
                        tmp_data += x.tolist()
                for d in tmp_data:
                    for y in d["results"]:
                        result.append({
                            "plate": y["plate"],
                            "province": y["province"],
                            "confidence": y["confidence"],
                            "time": y["time"],
                            "camera": d["camera"],
                        })
                # event_loop.close()
            return result
        except Exception as e:
            print("Error combining tmp data\n", e)
        return None

    @staticmethod
    async def get_tmp_images(data: list) -> list:
        """
        Get the images of plates being uploaded
        :param data:
        :return:
        """
        result = []
        try:
            for x in data:
                t = datetime.strptime(x["time"], "%Y-%m-%d %H:%M:%S")
                image_tmp = await CacheHandler.load("tmp/images", t.strftime("%Y-%m-%d %H:%M"))
                if image_tmp is not None:
                    list_tmp = image_tmp.tolist()
                    for p in list_tmp:
                        for y in p["results"]:
                            if x["plate"] == y["plate"]:
                                q = [q for q in result if x["plate"] == q["plate"]]
                                if len(q) == 0:
                                    result.append(
                                        {"plate": x["plate"], "province": x["province"], "confidence": x["confidence"],
                                         "time": x["time"], "camera": x["camera"], "image": y["image"]})
                                    break
        except Exception as e:
            print("Getting Temp Images Failed", e)
        return result

    @staticmethod
    def convert_dict_to_tuple(dic: list) -> list:
        """
        Convert list of dictionaries into a list of tuples

        :param dic:
        :return:
        """

        result = []
        try:
            for row in dic:
                new_tuple = tuple(row.values())
                result.append(new_tuple)
        except Exception as e:
            print("Could not convert dict to tuple\n", e)
        return result

    @staticmethod
    async def improve_confidence(dic: list) -> list or None:
        """
        Accept list of dictionaries and improve the confidence of the numberplate data it contains

        :param dic:
        :return: Returns list of dictionaries
        """
        try:
            tuple_list = CachedNumberplateHandler.convert_dict_to_tuple(dic)
            result = await NumberplateHandler.improve([x[:-1] for x in tuple_list])
            if result is not None:
                if len(result) > 0:
                    non_duplicates = NumberplateHandler.remove_similar(result)
                    if non_duplicates is not None:
                        out = []
                        for plate in non_duplicates:
                            row = [x for x in tuple_list if x[0] == plate[0] and x[3] == plate[3]]
                            if len(row) > 0:
                                out.append(
                                    {"plate": plate[0], "province": plate[1], "confidence": plate[2], "time": plate[3],
                                     "camera": row[0][4]})
                        return out
        except Exception as e:
            print("Cached Improve Confidence Error\n", e)

        return None

    @staticmethod
    async def compare_to_cached(data: list) -> [list, list]:
        """
        Compare current data to current hour cache
        :param data:
        :return:
        """
        now = datetime.now().strftime("%Y-%m-%d %H")
        cached_data = await CacheHandler.load("cache", now)
        in_cache = []
        out_cache = []
        if cached_data is not None:
            cached_data = cached_data.tolist()

            for plate in data:
                d = [x for x in cached_data if x["plate"] == plate["plate"]]
                if len(d) > 0:
                    in_cache.append(plate)
                else:
                    out_cache.append(plate)
        else:
            out_cache = data
        return in_cache, out_cache

    @staticmethod
    async def compare_to_uploaded(data: list) -> list or None:
        """
        Compare current data to the previously uploaded data
        :param data:
        :return:
        """

        def date_key(p):
            return datetime.now().strptime(p[3], "%Y-%m-%d %H:%M:%S")

        try:
            uploaded_cache = await CacheHandler.load("uploaded", datetime.now().strftime("%Y-%m-%d"))
            result = []
            if uploaded_cache is not None:
                if len(uploaded_cache) > 0:
                    uploaded_cache = uploaded_cache.tolist()
                    # Compare time of current data to the time of the uploaded data
                    for y in data:
                        same_time = [x for x in uploaded_cache if x[0] == y["plate"] and x[3] == y["time"]]
                        if len(same_time) == 0:
                            # Since uploaded list and current data don't share the same time we need to check if they are at
                            # least 1 min apart and confidence is at least 0.3 difference
                            already_uploaded = [x for x in uploaded_cache if x[0] == y["plate"]]
                            if len(already_uploaded) > 0:
                                already_uploaded_max_time = max(already_uploaded, key=lambda x: date_key(x))
                                time_diff = datetime.strptime(y["time"], "%Y-%m-%d %H:%M:%S") - datetime.strptime(
                                    already_uploaded_max_time[3], "%Y-%m-%d %H:%M:%S")
                                conf_diff = float(y["confidence"]) - float(already_uploaded_max_time[2])
                                if timedelta(minutes=1) < time_diff and conf_diff > 0.3:
                                    result.append(y)
                            else:
                                result.append(y)
            else:
                result = data

            return result
        except Exception as e:
            print("Compare to uploaded cache Error\n", e)
            pass
        return None
