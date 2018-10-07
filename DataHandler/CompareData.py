import random
from collections import Counter
from itertools import groupby, islice


class CompareData:

    """Return List if some aren't in the file else return None"""
    @staticmethod
    def compare_list_tuples(list1, list2, tuple_elem=0):
        dup = [x for x in list1 if x[tuple_elem] in list2]
        if len(dup) > 0:
            dup = CompareData.improve_confidence(dup)
            print("dups", dup)
        res = [x for x in list1 if x[tuple_elem] not in list2]
        return res, dup

    """Returns the cleaned array of duplicates and the counts of each duplicate"""
    @staticmethod
    def del_duplicates_list_tuples(l, tuple_elem=0):
        counts = list(Counter([x[tuple_elem] for x in l]).values())
        gen = (random.choice(tuple(g)) for _, g in groupby(l, key=lambda x: x[tuple_elem]))
        out = list(islice(gen, 4))
        return out, counts

    @staticmethod
    def improve_confidence(plates):
        for x in range(0, len(plates)):
            (pl, pr, con, t, img) = plates[x]
            con = round(con + 0.5, 2)
            plates[x] = (pl, pr, con, t, img)
        return plates