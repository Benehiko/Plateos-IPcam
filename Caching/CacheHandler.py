import gzip
import os
import pathlib
from pathlib import Path

import numpy as np

from DataHandler.CompareData import CompareData


class CacheHandler:

    @staticmethod
    def save(dir, filename, arr):
        pathlib.Path(dir).mkdir(parents=False, exist_ok=True)
        fi = Path(dir+filename + ".npy.gz")
        r = []
        if fi.exists():
            np_cached = CacheHandler.load(dir, filename)
            if np_cached is not None:
                try:
                    cached = np_cached[:, 0].tolist()
                    res = CompareData.compare_list_tuples(arr, cached)
                    if len(res) > 0:
                        r = [x[0:4] for x in res]
                        arr = np.append(arr=np.array(res, dtype=object), values=np_cached, axis=0)
                    else:
                        return
                except Exception as e:
                    print("Error on cached array", e)

        else:
            r = [x[0:4] for x in arr]
            arr = np.array(arr, dtype=object)

        f = gzip.GzipFile(dir+filename + ".npy.gz", "w")
        np.save(file=f, arr=arr)
        f.close()
        return r

    @staticmethod
    def load(dir, filename):
        pathlib.Path(dir).mkdir(parents=False, exist_ok=True)
        f = gzip.GzipFile(dir+filename + ".npy.gz", "r")
        try:
            arr = np.load(file=f)
        except Exception as e:
            print("Error on loading array", e)
            return None
        f.close()
        return arr

    @staticmethod
    def remove(dir, filename):
        pathlib.Path(dir).mkdir(parents=False, exist_ok=True)
        fi = Path(dir + filename + ".npy.gz")

        if fi.exists():
            os.remove(str(fi.resolve()))
