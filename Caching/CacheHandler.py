import gzip
import os
import pathlib
from pathlib import Path

import numpy as np

from DataHandler.CompareData import CompareData


# noinspection PyTypeChecker
class CacheHandler:

    @staticmethod
    def save(directory, filename, arr):
        try:
            pathlib.Path(directory).mkdir(parents=False, exist_ok=True)
            fi = Path(directory + filename + ".npy.gz")
            r = []
            if fi.exists():
                np_cached = CacheHandler.load(directory, filename)
                if np_cached is not None:
                    try:

                        cached = np_cached[:, 0].tolist()
                        res, dup = CompareData.compare_list_tuples(arr, cached)
                        if len(res) > 0:
                            r = [x[0:4] for x in res]
                            # arr = np.append(arr=np.array(res, dtype=object), values=np_cached, axis=0)
                            f = gzip.GzipFile(directory + filename + ".npy.gz", "a")
                            np.save(file=f, arr=r)
                            f.close()
                        if len(dup) > 0:
                            r += [x[0:4] for x in dup]
                    except Exception as e:
                        print("Error on cached array", e)

            else:
                r = [x[0:4] for x in arr]
                arr = np.array(arr, dtype=object)
                f = gzip.GzipFile(directory + filename + ".npy.gz", "w")
                np.save(file=f, arr=arr)
                f.close()

            return r
        except Exception as e:
            print(e)
            pass

        return None

    @staticmethod
    def load(directory, filename):
        pathlib.Path(directory).mkdir(parents=False, exist_ok=True)
        f = gzip.GzipFile(directory + filename + ".npy.gz", "r")
        try:
            arr = np.load(file=f)
        except Exception as e:
            print("Error on loading array", e)
            return None
        f.close()
        return arr

    @staticmethod
    def remove(directory, filename):
        try:
            pathlib.Path(directory).mkdir(parents=False, exist_ok=True)

            with Path(directory + filename + ".npy.gz") as fi:
                if fi.exists():
                    os.remove(str(fi.resolve()))
        except Exception as e:
            print(e)
            pass
