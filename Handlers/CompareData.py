from collections import Counter
from datetime import datetime
from itertools import groupby


class CompareData:

    # TODO: Add type mapping and return types to methods with correct descriptions

    """Return List if some aren't in the file else return None"""

    @staticmethod
    def compare_list_tuples(list1, list2):
        dup = [x for x in list1 for y in list2 if x["plate"] == y["plate"]]
        res = [x for x in list1 if x["plate"] not in list2]
        return res, dup

    @staticmethod
    def del_duplicates_list_tuples(l: list) -> [list, int] or [None, None]:
        """
        Cleans list of tuples of any duplication while maintaining order of time (most recent preferred).
        :param l:
        :return: returns list of tuples and amount of duplicates (per plate).
        """

        def date_key(p, pos, dateformat):
            return datetime.strptime(p[pos], dateformat)

        try:
            counts = list(Counter([x[0] for x in l]).values())
            out = [list(g)[0] for _, g in groupby(l, key=lambda x: x[0])]
            result = []
            for x in out:
                tmp = [y for y in l if y[0] == x[0]]
                max_time = max(tmp, key=lambda p: date_key(p, 3, "%Y-%m-%d %H:%M:%S"))
                result.append(max_time)

            return result, counts
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
