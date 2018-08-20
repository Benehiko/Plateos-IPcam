from collections import Counter
from difflib import SequenceMatcher

'''
                CASE LETTERS: Literal letters in the numberplate
                a: compulsory letter (A - Z)
                b: letter (A - Z) or nothing
                x: compulsory character (A - Z, 0 - 9)
                z: character (A - Z, 0 - 9) or nothing
                +: a compulsory digit (0 - 9)

                NB:Vowels are not used on private vehicles.

                https://en.wikipedia.org/wiki/Vehicle_registration_plates_of_South_Africa
                Western Province: xzzzzz wp
                KwaZulu-Natal: zn
                Mpumalanga Province: mp
                Eastern Cape Province: ec
                Limpopo Province: l
                Gauteng Province: gp
                Northen Cape Province: nc
                Free State: fs
                North West Province: nw
                Diplomatic Vehicles: +++(d or s) +++d or +++(d or s) bbb +++d
                National Government Vehicles: Gaa +++ G
                Police Vehicles: Baa+++ B
                Military Vehicles: aaa+++ M

'''


class Numberplate:

    @staticmethod
    def validate(text, use_provinces=False):
        if use_provinces:
            result = None
            confidence = 0

            if 2 <= len(text) <= 9:
                result, confidence = Numberplate.province_validate(text)
                if confidence == 0:
                    result, confidence = Numberplate.special_plate_validate(text)

            return result, confidence

        return 3 <= len(text) <= 9

    @staticmethod
    def improve(plates):
        tmp = Numberplate.remove_duplicates(plates)
        out = []
        while True:
            highest = Numberplate.get_highest(tmp)
            if highest is not None:
                result, remainder = Numberplate.split_plates(tmp, highest)
                out.append(result)
                if len(remainder) < 0:
                    break
                else:
                    tmp = remainder
            else:
                break
        return out

    @staticmethod
    def sanitise(text):
        text = text.replace("\n", "")
        text = ''.join(e for e in text if e.isalnum()).upper()
        return text

    @staticmethod
    def province_validate(text):
        result = ""
        confidence = 0

        provinces_pre = ["MP", "EC", "GP", "NC", "FS", "NW", "L", "WP", "ZN"]

        provinces_post = ["N", "C"]

        if text[-2:] in provinces_pre:
            pre = text[-2:]
            if len(text) == 8:
                if text[0:3].isalpha() and text[3:6].isnumeric():
                    if pre == "MP":
                        result = "Mpumalanga"
                    elif pre == "EC":
                        result = "Eastern Cape"
                    elif pre == "NC":
                        result = "Northern Cape"
                    elif pre == "FS":
                        result = "Free State"
                    elif pre == "NW":
                        result = "North West"
                    elif pre == "GP":
                        result = "Gauteng"
                    elif text[-1:] == "L":
                        result = "Limpopo"
                    confidence = 0.8
                elif text[0:2].isalpha() and text[2:4].isnumeric() and text[4:6].isalpha():
                    if pre == "GP":
                        result = "Gauteng"
                        confidence = 0.8

            elif len(text) > 2:
                if text[0].isalnum():
                    if pre == "MP":
                        result = "Mpumalanga"
                        confidence = 0.5
                    elif pre == "EC":
                        result = "Eastern Cape"
                        confidence = 0.5
                    elif pre == "NC":
                        result = "Northern Cape"
                        confidence = 0.5
                    elif pre == "FS":
                        result = "Free State"
                        confidence = 0.5
                    elif pre == "NW":
                        result = "North West"
                        confidence = 0.5
                    elif pre == "GP":
                        result = "Gauteng"
                        confidence = 0.5
                    elif pre == "WP":
                        result = "Western Cape"
                        confidence = 0.5
                    elif pre == "ZN":
                        result = "KwaZulu-Natal"
                        confidence = 0.5
                    elif text[-1:] == "L":
                        result = "Limpopo"
                        confidence = 0.5
            elif len(text) == 2:
                if text[-1:] == "L":
                    result = "Limpopo"
                    confidence = 0.5

        if text[1] in provinces_post:
            if text[1].isalpha():
                if text[0] == "C":
                    result = "Western Cape"
                elif text[0] == "N":
                    result = "KwaZulu-Natal"
                confidence = 0.8

        return result, confidence

    @staticmethod
    def special_plate_validate(text):

        specials = ["B", "D", "G", "M"]
        confidence = 0
        result = ""

        if text[-1] or text[0] in specials:
            if len(text) == 7:
                if (text[1:3].isalpha() or text[0:3].isalpha()) and text[3:6].isnumeric():
                    pre = text[-1]
                    post = text[0]
                    if pre == "B":
                        if post == "B":
                            result = "Police"
                            confidence = 0.8
                    elif pre == "G":
                        if post == "G":
                            result = "Government Vehicle"
                            confidence = 0.8
                    elif pre == "M":
                        result = "Military Vehicle"
                        confidence = 0.8

        return result, confidence

    """
        Remove all the duplicates.
        Returns list without duplicates with increased confidence.
    """
    @staticmethod
    def remove_duplicates(l):

        """Get duplication count of each element"""
        counts = list(Counter([x[0] for x in l]).values())

        """Remove duplicates using set then convert back to list"""
        plates = set(l)
        plates = list(plates)

        for x in range(0, len(plates)):
            (pl, pr, con) = plates[x]
            con = con + (counts[x] / 100)
            plates[x] = (pl, pr, con)

        return plates

    """Get the highest confidence value"""
    @staticmethod
    def get_highest(l):
        if len(l) > 0:
            highest = l[0]
            for x in range(0, len(l)):
                _, _, con = l[x]
                _, _, h = highest
                if h < con:
                    highest = l[x]

            return highest
        return None

    """
        Split plates based off of their similarity report
        Returns The best plate (confidence level highest)
        Returns the remainder that was not similar
    """
    @staticmethod
    def split_plates(plates, highest):
        remainder = []
        similar = []
        for x in plates:
            if SequenceMatcher(None, highest[0], x[0]).ratio() * 100 > 80:
                similar.append(x)
            else:
                remainder.append(x)

        r = max(similar, key=lambda x: x[2])
        return r, remainder
