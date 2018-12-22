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
        result = []
        try:
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
            fi = pathlib.Path(directory + "/" + filename + ".npy.gz")

            # The file exists so lets append
            if fi.exists():

                # Load in the existing cache data
                cached = CacheHandler.load(directory, filename)
                if cached is not None:
                    # Get all the numberplates into a list.
                    cached_plates = cached[:, 0].tolist()

                    # Compare current data to cache for duplicates
                    res, dup = CompareData.compare_list_tuples(arr, cached_plates)

                    # Non-dups gets added to the file and then added to result array for post
                    if len(res) > 0:
                        result += [x[0:4] for x in res]
                        rest = np.array(res, dtype=object)
                        out = np.concatenate((cached, rest), axis=0)
                        f = gzip.GzipFile(directory + "/" + filename + ".npy.gz", "w")
                        np.save(file=f, arr=out)
                        f.close()

                    # Duplicates got an increase in confidence and then added to result for post
                    if len(dup) > 0:
                        result += [x[0:4] for x in dup]

            # The file doesn't exist. Create a new one with the current data.
            else:
                result = [x[0:4] for x in arr]
                arr = np.array(arr, dtype=object)
                f = gzip.GzipFile(directory + "/" + filename + ".npy.gz", "w")
                np.save(file=f, arr=arr)
                f.close()

            # Return the result even though it might be empty.
            return result
        except Exception as e:
            print(e)
            pass
        return None  # Exception is thrown

    @staticmethod
    def load(directory, filename):
        fi = pathlib.Path(directory + "/" + filename + ".npy.gz")
        if fi.exists():
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)
            f = gzip.GzipFile(directory + "/" + filename + ".npy.gz", "r")
            try:
                arr = np.load(file=f)
            except Exception as e:
                print("Error on loading array", e)
                return None
            f.close()
            return arr
        return None

    @staticmethod
    def remove(directory, filename):
        try:
            pathlib.Path(directory).mkdir(parents=True, exist_ok=True)

            with Path(directory + "/" + filename + ".npy.gz") as fi:
                if fi.exists():
                    os.remove(str(fi.resolve()))
        except Exception as e:
            print(e)
            pass

    @staticmethod
    def loadByPlate(directory, filename, plate):
        try:
            data = CacheHandler.load(directory, filename)
            d = [x for x in data if x[0] == plate]
            return d
        except Exception as e:
            print(e)
            pass
        return []
