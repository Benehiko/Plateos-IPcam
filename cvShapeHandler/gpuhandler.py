import cv2


class GPUHandler:


    @staticmethod
    def toUmat(mat):
        return cv2.UMat(mat)

    @staticmethod
    def getMat(umat):
        return umat.get()

