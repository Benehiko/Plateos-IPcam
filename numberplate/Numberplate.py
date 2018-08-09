from difflib import SequenceMatcher
import numpy as np

class Numberplate:

    def __init__(self, min=3, max=10, use_provinces=False):
        self.min = min
        self.max = max
        self.provinces = use_provinces

    def isPlate(self, text):
        if self.provinces:
            provinces = ["gp", "mp", "l", "ca", "zn", "ec", "nw", "nc", "fs", "d", "g", "b", "m", "wp"]

        return 3 <= len(text) < 10

    def getBetter(self, *plates):
        chance = 0
        carcount = 0

        bestPlate = ""
        compressed, count = np.unique(plates, return_counts=True)
        print(compressed)
        return compressed


    def sanitise(self, text):
        text = text.replace("\n", "")
        text = ''.join(e for e in text if e.isalnum()).upper()
        return text




