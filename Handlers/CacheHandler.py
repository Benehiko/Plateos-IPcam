import asyncio
import copy
import os
import pathlib
from os import listdir
from os.path import isfile, join
from pathlib import Path
from threading import Event

import numpy as np

from Handlers.CompareData import CompareData

# noinspection PyTypeChecker

event = Event()


class CacheHandler:
    # TODO: Add type mapping and return types to methods with correct descriptions
    base = "../plateos-files/"
    load_lock = asyncio.Lock()
    tmp_lock = asyncio.Lock()
    cache_lock = asyncio.Lock()
    meta_lock = asyncio.Lock()
    upload_lock = asyncio.Lock()

    @staticmethod
    async def save_cache(directory, filename, arr):
        with (await CacheHandler.cache_lock):
            result = []
            try:
                pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
                fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
                pathlib.Path(CacheHandler.base + directory + "/images/").mkdir(parents=True, exist_ok=True)
                fi2 = pathlib.Path(CacheHandler.base + directory + "/images/" + filename + ".npz")

                # The file exists so lets append
                if fi.exists():

                    # Load in the existing cache data
                    cached = await CacheHandler.load(CacheHandler.base + directory, filename)
                    if cached is not None:
                        # Compare current data to cache for duplicates
                        res, dup = CompareData.compare_list_tuples(arr, copy.deepcopy(cached.tolist()))
                        # Non-dups gets added to the file
                        if len(res) > 0:
                            rest = np.array(res)
                            out = np.concatenate((cached, rest))
                            np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)

                # The file doesn't exist. Create a new one with the current data.
                else:
                    out = np.array(arr)
                    np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)

                if fi2.exists():
                    cached = await CacheHandler.load(CacheHandler.base + directory + "/images", filename)
                    if cached is not None:
                        res, dup = CompareData.compare_list_tuples(arr, copy.deepcopy(cached.tolist()))
                        # Non-dups gets added to the file
                        if len(res) > 0:
                            rest = np.array(res)
                            out = np.concatenate((cached, rest))
                            np.savez_compressed(CacheHandler.base + directory + "/images/" + filename, a=out)
                else:
                    out = np.array(arr)
                    np.savez_compressed(CacheHandler.base + directory + "/images/" + filename, a=out)

                # Return the result even though it might be empty.
                return result
            except Exception as e:
                print("Cache", e)
                pass
        return None  # Exception is thrown

    @staticmethod
    async def update_plate_cache(filename, arr):
        with (await CacheHandler.cache_lock):
            result = []

            try:
                pathlib.Path(CacheHandler.base + "cache/").mkdir(parents=True, exist_ok=True)
                fi = pathlib.Path(CacheHandler.base + "cache/" + filename + ".npz")

                if fi.exists():
                    cached = await CacheHandler.load("cache", filename)
                    if cached is not None:
                        cached = cached.tolist()
                        for c in cached:
                            t = [x for x in arr if c["plate"] == x["plate"]]
                            if len(t) > 0:
                                # t = max(t, key=lambda x: plate_conf(x))
                                result += t
                            else:
                                result.append(c)
                        rest = np.array(result)
                        np.savez_compressed(CacheHandler.base + "cache/" + filename, a=rest)

            except Exception as e:
                print("Update Cache Plate Error\n", e)
                pass

    @staticmethod
    async def load(directory, filename) -> np.ndarray or None:
        with (await CacheHandler.load_lock):
            pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
            fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
            if fi.exists():
                try:
                    arr = np.load(CacheHandler.base + directory + "/" + filename + ".npz")["a"]
                    # return arr
                except Exception as e:
                    print("Error on loading array", e)
                    CacheHandler.remove(directory, filename)
                else:
                    return arr
        return None

    @staticmethod
    def remove(directory, filename):
        try:
            pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)

            with Path(CacheHandler.base + directory + "/" + filename + ".npz") as fi:
                if fi.exists():
                    os.remove(str(fi.resolve()))
        except Exception as e:
            print(e)
            pass

    @staticmethod
    async def loadByPlate(directory, filename, plate):
        try:
            data = await CacheHandler.load(CacheHandler.base + directory, filename)
            if data is not None:
                tmp = data.tolist()
                d = [x for x in tmp if x["plate"] == plate]
                return d
        except Exception as e:
            print(e)
            pass
        return []

    @staticmethod
    async def save_meta(directory: str, filename: str, arr: list):
        with (await CacheHandler.meta_lock):
            try:
                pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
                fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
                array = np.array([arr])
                if fi.exists():
                    # Load in the existing cache data
                    cached = CacheHandler.load(CacheHandler.base + directory, filename)
                    if cached is not None:
                        out = np.concatenate((cached, array))
                        np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)
                else:
                    np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=array)

            except Exception as e:
                print("Error on saving meta", e)
                pass

    @staticmethod
    async def save_upload(directory: str, filename: str, arr: list):
        with (await CacheHandler.upload_lock):
            try:
                if len(arr) > 0:
                    pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
                    fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
                    if fi.exists():
                        # Load in the existing cache data
                        cached = await CacheHandler.load(CacheHandler.base + directory, filename)
                        if cached is not None:
                            out = np.array(arr)
                            out = np.concatenate((cached, out))
                            np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)
                    else:
                        out = np.array(arr)
                        np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)
            except Exception as e:
                print("Error saving upload data", e)

    @staticmethod
    async def save_tmp(directory: str, filename: str, arr: list):
        with (await CacheHandler.tmp_lock):
            try:
                if len(arr) > 0:
                    pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
                    fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
                    pathlib.Path(CacheHandler.base + directory + "/images/").mkdir(parents=True, exist_ok=True)
                    fi2 = pathlib.Path(CacheHandler.base + directory + "/images" + filename + ".npz")
                    only_text = []
                    for y in arr:
                        camera = y["camera"]
                        results = [{"plate": x["plate"], "country": x["country"], "province": x["province"],
                                    "confidence": x["confidence"],
                                    "time": x["time"], "char-len": x["char-len"]} for x in y["results"]]
                        only_text.append({"camera": camera, "results": results})
                    if fi.exists():
                        # Load in the existing cache data
                        cached = await CacheHandler.load(CacheHandler.base + directory, filename)
                        if cached is not None:
                            out = np.array(only_text)
                            out = np.concatenate((cached, out))
                            np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)
                    else:
                        out = np.array(only_text)
                        np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)

                    if fi2.exists():
                        cached = await CacheHandler.load(CacheHandler.base + directory + "/images", filename)
                        if cached is not None:
                            out = np.array(arr)
                            out = np.concatenate((cached, out))
                            np.savez_compressed(CacheHandler.base + directory + "/images/" + filename, a=out)
                    else:
                        out = np.array(arr)
                        np.savez_compressed(CacheHandler.base + directory + "/images/" + filename, a=out)

            except Exception as e:
                print("Error saving temp", e)
                pass

    @staticmethod
    def get_file_list(directory: str) -> list:
        pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
        files = [f.replace('.npz', '') for f in listdir(CacheHandler.base + directory + "/") if
                 isfile(join(CacheHandler.base + directory, f))]
        return files
