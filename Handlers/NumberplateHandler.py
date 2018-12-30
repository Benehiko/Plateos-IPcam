import copy
import pathlib
import re
from difflib import SequenceMatcher
from os import listdir
from os.path import isfile, join

from Handlers.CacheHandler import CacheHandler
from Handlers.CompareData import CompareData
from Handlers.PropertyHandler import PropertyHandler


class NumberplateHandler:

    @staticmethod
    def validate(plate):
        """
        Validate numberplate by using the template matching given by numberplate.yml
        PLEASE NOTE: This function has a problem:
        1. Ignores COMPULSORY numbers in the regex
           - eg. ab+++ [ZERRR] would be seen as valid (no number present).

        :param plate:
        :return:
        """
        try:
            data = PropertyHandler.numberplate["Country"]
            confidence_rule = PropertyHandler.numberplate["Confidence"]

            for country in data:
                for province in data[country]:

                    standard_regex = data[country][province]["standard"]
                    custom_regex = data[country][province]["custom"]
                    code = data[country][province]["code"]
                    min_val, max_val = NumberplateHandler.get_min_max(standard_regex + custom_regex, code)

                    if min_val <= len(plate) <= max_val:

                        valid_province = NumberplateHandler.contains_province(plate, standard_regex + custom_regex,
                                                                              code)
                        if False not in valid_province:
                            if valid_province[1] in standard_regex:
                                plate_type = "standard"
                            elif valid_province[1] in custom_regex:
                                plate_type = "custom"
                            else:
                                break
                            confidence = float(confidence_rule[plate_type]) + (
                                    float(confidence_rule["code-char-value"]) * len(max(valid_province[0], key=len)))
                            return country, province, confidence
        except Exception as e:
            print("Numberplate Validator Error", "\n", e)
            pass
        return None, None, None

    @staticmethod
    def code_position(val):
        """
        Finds the position of area code using the template matching code [!, ?]
        :param val:
        :return:
        """
        pos = val.find('!')
        if pos == -1:
            pos = val.find("?")
            if pos > -1:
                if pos == len(val) - 1:
                    return "any"
        else:
            if pos == len(val) - 1:
                return "end"
            elif pos == 0:
                return "start"
        return ""

    @staticmethod
    def code_plate_pos(plate, pos, code_len):
        pos_val = []
        for p in pos:
            if p + code_len == len(plate):
                pos_val.append("end")
            elif p == 0:
                pos_val.append("start")
            else:
                pos_val.append("any")
        return pos_val

    @staticmethod
    def code_parse(value, char, nothing_counter):
        """
        Parse regex with the following patterns.
         - a compulsory alpha
         - + compulsory numberic
         - z non compulsory alphanum
         - n non compulsory numeric
         - b non compulsory alpha
         - x compulsory alphanum
         - X any capital letter is seen as a string literal
        :param value:
        :param char:
        :param nothing_counter: Amount of chars non compulsory
        :return:
        """
        if value == 'a':
            return char.isalpha()
        elif value == '+':
            return char.isnumeric()
        elif value == 'x':
            return char.isalnum()
        elif value == 'z':
            return char.isalnum()
        elif value == 'n':
            if char.isnumeric():
                return True
            else:
                if nothing_counter[0] > 0:
                    nothing_counter[0] -= 1
                    return True
        elif value == 'b':
            if char.isalnum():
                return True
            else:
                if nothing_counter[0] > 0:
                    nothing_counter[0] -= 1
                    return True
        elif value == char:
            return True
        return False

    @staticmethod
    def get_regex_length(regex):
        counter = 0
        for r in regex:
            if r not in ['n', 'z', 'b']:
                counter += 1
        return counter

    @staticmethod
    def get_min_max(regex, code):
        c = [x.replace('!', '').replace('?', '') for x in code]
        max_plate = max(regex, key=len)
        max_province = max(c, key=len)
        min_plate = min([x.replace('b', '').replace('z', '').replace('n', '') for x in regex], key=len)
        min_province = min(c, key=len)
        return len(min_plate.replace('c', min_province)), len(max_plate.replace('c', max_province))

    @staticmethod
    def contains_province(plate, regex, code):
        try:
            # Regex match string, contains positions of allowed characters
            for reg in regex:
                # Find all positions of our enforced 'code' on the plate
                pos = [i for i, letter in enumerate(reg) if letter == 'c']  # c = code

                if len(pos) > 0:
                    # Find all codes which it might be
                    val = [c.replace('!', '').replace('?', '') for c in code if
                           NumberplateHandler.contains_province_helper(plate=plate, code=c, code_occurances=pos,
                                                                       regex=reg.replace('c', ''))]
                    if len(val) > 0:
                        return val, reg
        except Exception as e:
            print("Contains Province Error\n", e)
            pass
        return False, False

    @staticmethod
    def pos_regex_code(code_occurances, regex):
        if len(code_occurances) > 1:
            return "any"
        if code_occurances[0] == 0:
            return "start"
        if code_occurances[0] >= len(regex):
            return "end"

    @staticmethod
    def pos_plate_code(plate, code, code_occurances, regex):
        """
        Validate if the plate has area code in the same position as the regex template
        :param plate: numberplate
        :param code: region code of plate
        :param code_occurances: Amount of occurences of region code in regex
        :return:
        """
        try:
            c_pos = NumberplateHandler.code_position(code)
            r_pos = NumberplateHandler.pos_regex_code(code_occurances, regex)
            t_code = code.replace('!', '').replace('?', '')
            code_len = len(t_code)
            pos = [w.start() for w in re.finditer(t_code, plate)]
            if len(pos) == len(code_occurances):
                plate_pos = NumberplateHandler.code_plate_pos(plate, pos, code_len)
                counter = 0
                tmp = ""
                for p in plate_pos:
                    if p == c_pos == r_pos:
                        if p == "end":
                            if plate[-code_len:] == t_code:
                                tmp = plate[:-code_len]
                                counter += 1
                        elif p == "start":
                            if plate[0:code_len] == t_code:
                                tmp = plate[code_len:]
                                counter += 1
                        elif p == "any":
                            for x in pos:
                                if plate[x:code_len] == t_code:
                                    sub1 = plate[:x]
                                    sub2 = plate[x + code_len:]
                                    tmp = sub1 + sub2
                                    counter += 1

                if counter == len(pos):
                    return tmp
        except Exception as e:
            print("Plate code position error\n", e)
            pass
        return False

    @staticmethod
    def contains_province_helper(plate, code, code_occurances, regex):
        try:
            c_less_plate = NumberplateHandler.pos_plate_code(plate, code, code_occurances, regex)
            if c_less_plate is not False and len(c_less_plate) > 0:
                if NumberplateHandler.get_regex_length(regex) <= len(c_less_plate) <= len(regex):
                    nothing_counter = [len(regex) - len(c_less_plate)]
                    return NumberplateHandler.parse_helper(regex, c_less_plate, 0, len(c_less_plate) - 1,
                                                           nothing_counter)
        except Exception as e:
            print("Contains Province Helper Error\n", e)
            pass
        return False

    @staticmethod
    def parse_helper(regex, plate, pos, end, nothing_counter):
        if pos > end:
            return True
        if NumberplateHandler.code_parse(regex[pos], plate[pos], nothing_counter):
            return NumberplateHandler.parse_helper(regex, plate, pos + 1, end, nothing_counter)
        return False

    @staticmethod
    def improve(plates):
        tmp_copy = copy.deepcopy(plates)
        tmp = NumberplateHandler.remove_duplicates(plates)
        if tmp is not None:
            for i in range(0, len(tmp)):
                val, cached_plate = NumberplateHandler.search_in_cache(tmp[i])
                if val > 0:
                    cache_conf = 0
                    for x in cached_plate:
                        cache_conf += (x["confidence"])
                    cache_conf = (cache_conf / val)
                    (pl, pr, con, t) = tmp[i]
                    con = round(float(con + (cache_conf / 100)), 2)
                    tmp[i] = (pl, pr, con, t)
            out = []
            while True:
                highest = NumberplateHandler.get_highest(tmp)
                if highest is not None:
                    result, remainder = NumberplateHandler.split_plates(tmp, highest)
                    if result is not None:
                        old_conf = [x for x in tmp_copy if x[0] == result[0] and x[3] == result[3]]
                        if len(old_conf) > 0:
                            diff = float(result[2] - old_conf[0][2])
                            if diff >= float((PropertyHandler.numberplate["Confidence"]["min-deviation"])):
                                out.append(result)

                        if len(remainder) == 0:
                            break
                        else:
                            tmp = remainder
                else:
                    break
            return out
        return None

    @staticmethod
    def search_in_cache(plate):
        count = 0
        cached_plates = []
        try:
            pathlib.Path("cache").mkdir(parents=True, exist_ok=True)
            files = [f.replace('.npz', '') for f in listdir("cache") if isfile(join("cache", f))]
            for filename in files:
                data = CacheHandler.loadByPlate("cache", filename, plate)
                cached_plates += data
                count = count + len(data)
        except Exception as e:
            print(e)
            pass
        return count, cached_plates

    @staticmethod
    def remove_similar(plates):
        result = []
        highest = NumberplateHandler.get_highest(plates)
        if highest is not None:
            result.append(highest)
            for x in plates:
                if x[0] is not highest[0]:
                    if SequenceMatcher(None, highest[0], x[0]).ratio() * 100 < 80:
                        result.append(x)
        return result

    @staticmethod
    def sanitise(text):
        try:
            text = text.replace("\n", "")
            text = ''.join(e for e in text if e.isalnum()).upper()
            return text
        except Exception as e:
            print("Sanitise Error", e)
            pass
        return ""

    @staticmethod
    def remove_duplicates(l):
        """
        Remove all the duplicates.
        Returns list without duplicates with increased confidence.
        """
        if len(l) > 0:
            plates, counts = CompareData.del_duplicates_list_tuples(l)
            if plates is not None or counts is not None:
                for x in range(0, len(counts)):
                    (pl, pr, con, t) = plates[x]
                    con = round(con + (counts[x] * 10 / 100), 2)
                    plates[x] = (pl, pr, con, t)

                return plates
        return None

    @staticmethod
    def get_highest(l):
        """Get the highest confidence value"""
        if len(l) > 0:
            highest = l[0]
            for x in l:
                _, _, con, _ = x
                _, _, h, _ = highest
                if h < con:
                    highest = x
            return highest
        return None

    # noinspection PyShadowingNames
    @staticmethod
    def split_plates(plates, highest):
        """
            Split plates based off of their similarity report
            Returns The best plate (confidence level highest)
            Returns the remainder that was not similar
        """
        remainder = []
        similar = []
        if len(plates) > 0 and len(highest) > 0:
            for x in plates:
                if SequenceMatcher(None, highest[0], x[0]).ratio() * 100 > 70:
                    similar.append(x)
                else:
                    remainder.append(x)
        if len(similar) > 0:
            r = max(similar, key=lambda x: x[2])
        else:
            r = None
        return r, remainder
