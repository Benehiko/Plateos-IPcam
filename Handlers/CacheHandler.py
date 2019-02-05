import copy
import json
import os
import pathlib
import time
from os import listdir
from os.path import isfile, join
from pathlib import Path
from threading import Event

import numpy as np

from Handlers.CompareData import CompareData
# noinspection PyTypeChecker
from cvlib.CvHelper import CvHelper

event = Event()


class CacheHandler:
    # TODO: Add type mapping and return types to methods with correct descriptions
    base = "../plateos-files/"

    @staticmethod
    def save_cache(directory, filename, arr):
        result = []
        try:
            pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
            fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
            pathlib.Path(CacheHandler.base + directory + "/images/").mkdir(parents=True, exist_ok=True)
            fi2 = pathlib.Path(CacheHandler.base + directory + "/images/" + filename + ".npz")

            # The file exists so lets append
            if fi.exists():

                # Load in the existing cache data
                cached = CacheHandler.load(CacheHandler.base + directory, filename)
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
                cached = CacheHandler.load(CacheHandler.base + directory + "/images", filename)
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
    def update_plate_cache(filename, arr):
        result = []

        try:
            pathlib.Path(CacheHandler.base + "cache/").mkdir(parents=True, exist_ok=True)
            fi = pathlib.Path(CacheHandler.base + "cache/" + filename + ".npz")

            if fi.exists():
                cached = CacheHandler.load("cache", filename)
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
    def load(directory, filename) -> np.ndarray or None:
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
    def loadByPlate(directory, filename, plate):
        try:
            data = CacheHandler.load(CacheHandler.base + directory, filename)
            if data is not None:
                tmp = data.tolist()
                d = [x for x in tmp if x["plate"] == plate]
                return d
        except Exception as e:
            print(e)
            pass
        return []

    @staticmethod
    def save_meta(directory: str, filename: str, arr: list):
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
    def save_upload(directory: str, filename: str, arr: list):
        try:
            if len(arr) > 0:
                pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
                fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
                if fi.exists():
                    # Load in the existing cache data
                    cached = CacheHandler.load(CacheHandler.base + directory, filename)
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
    def save_tmp(directory: str, filename: str, arr: list):
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
                    cached = CacheHandler.load(CacheHandler.base + directory, filename)
                    if cached is not None:
                        out = np.array(only_text)
                        out = np.concatenate((cached, out))
                        np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)
                else:
                    out = np.array(only_text)
                    np.savez_compressed(CacheHandler.base + directory + "/" + filename, a=out)

                if fi2.exists():
                    cached = CacheHandler.load(CacheHandler.base + directory + "/images", filename)
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
    def recover(directory, filename, outdir):
        try:
            pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
            pathlib.Path(CacheHandler.base + outdir + "/").mkdir(parents=True, exist_ok=True)
            fi = pathlib.Path(CacheHandler.base + directory + "/" + filename + ".npz")
            if fi.exists():
                cached = CacheHandler.load(CacheHandler.base + directory, filename)
                if cached is not None:
                    x = cached.tolist()
                    for i in x:
                        print("time", i["time"])
                        pathlib.Path(i["time"]).mkdir(parents=True, exist_ok=True)
                        CvHelper.write_mat(i["original"], outdir + "/" + i["time"] + "/", "original.jpg")
                        f = open(outdir + "/" + i["time"] + "/" + "data" + ".txt", "w+")
                        for y in i["results"]:
                            r = [value for key, value in y.items() if key not in {"image"}]
                            CvHelper.write_mat(y["image"], outdir + "/" + i["time"] + "/", y["time"] + ".jpg")
                            f.write(json.dumps(r) + "\n")

                        f.close()


        except Exception as e:
            print("Error recovering ", filename, "\nError:", e)
            pass

    @staticmethod
    def get_file_list(directory: str) -> list:
        pathlib.Path(CacheHandler.base + directory + "/").mkdir(parents=True, exist_ok=True)
        files = [f.replace('.npz', '') for f in listdir(CacheHandler.base + directory + "/") if
                 isfile(join(CacheHandler.base + directory, f))]
        return files
