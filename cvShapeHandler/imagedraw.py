import cv2


class ImageDraw:

    @staticmethod
    def draw(img, array, colour, thickness):
        col = ImageDraw.get_colour(colour)
        cv2.drawContours(img, array, -1, col, thickness)
        return img

    @staticmethod
    def get_colour(colour):
        col = (0, 255, 0)
        if colour == "Green":
            col = (0, 255, 0)
        elif colour == "Black":
            col = (0, 0, 0)
        elif colour == "Blue":
            col = (255, 0, 0)
        elif colour == "White":
            col = (255, 255, 255)
        elif colour == "Red":
            col = (0, 0, 255)

        return col

    @staticmethod
    def draw_text(img, text, position, colour, size, thickness):
        font = cv2.FONT_HERSHEY_SIMPLEX
        col = ImageDraw.get_colour(colour)
        cv2.putText(img, text, position, font, size, col, thickness)
        return img
