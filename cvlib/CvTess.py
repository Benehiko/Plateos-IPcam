import cv2


def ocr(mat):

    tesser = cv2.text.OCRTesseract_create()