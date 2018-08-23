import random
from collections import Counter
from itertools import groupby, islice


class CompareData:

    """Return List if some aren't in the file else return None"""
    @staticmethod
    def compare_list_tuples(list1, list2, tuple_elem=0):
        res = [x for x in list1 if x[tuple_elem] not in list2]
        return res

    """Returns the cleaned array of duplicates and the counts of each duplicate"""
    @staticmethod
    def del_duplicates_list_tuples(l, tuple_elem=0):
        counts = list(Counter([x[tuple_elem] for x in l]).values())
        gen = (random.choice(tuple(g)) for _, g in groupby(l, key=lambda x: x[tuple_elem]))
        out = list(islice(gen, len(l[0])-1))
        #print(out)
        return out, counts
