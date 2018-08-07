
class Numberplate:

    def __init__(self, min=3, max=10, use_provinces=False):
        self.min = min
        self.max = max
        self.provinces = use_provinces

    def isPlate(self, text):
        if self.provinces:
            provinces = ["gp", "mp", "l", "ca", "zn", "ec", "nw", "nc", "fs", "d", "g", "b", "m", "wp"]

        return 3 <= len(text) <10

