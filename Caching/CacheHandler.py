import numpy as np


class CacheHandler:

    @staticmethod
    def save(filename, arr):
        np.save(filename, arr)

    @staticmethod
    def load(filename):
        return np.load(filename)