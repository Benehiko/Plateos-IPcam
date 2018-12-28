import random
from collections import Counter
from itertools import groupby, islice


class CompareData:
    """Return List if some aren't in the file else return None"""

    @staticmethod
    def compare_list_tuples(list1, list2):
        dup = [x for x in list1 for y in list2 if x["plate"] == y["plate"]]
        # if len(dup) > 0:
        #     dup = CompareData.improve_confidence(dup)
        res = [x for x in list1 for y in list2 if x["plate"] != y["plate"]]
        return res, dup

    @staticmethod
    def del_duplicates_list_tuples(l):
        """Returns the cleaned array of duplicates and the counts of each duplicate"""
        try:
            counts = list(Counter([x[0] for x in l]).values())
            out = [list(g)[0] for _, g in groupby(l, key=lambda x: x[0])]
            return out, counts
        except Exception as e:
            print("Could not delete duplicates", e)
        return None, None

    @staticmethod
    def improve_confidence(plates):
        for x in range(0, len(plates)):
            (pl, pr, con, t, img) = plates[x]
            con = round(con + 0.5, 2)
            plates[x] = (pl, pr, con, t, img)
        return plates
