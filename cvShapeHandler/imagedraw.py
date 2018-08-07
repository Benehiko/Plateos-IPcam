import cv2


class ImageDraw:

    @staticmethod
    def draw(img, array, colour, thickness):
        col = (0, 255, 0)

        if colour == "Green":
            col = (0,255,0)
        elif colour == "Black":
            col = (0, 0, 0)
        elif colour == "Blue":
            col = (0, 0, 255)
        elif colour == "White":
            col = (255, 255, 255)
        
        cv2.drawContours(img, array, -1, col, thickness)
        return img
