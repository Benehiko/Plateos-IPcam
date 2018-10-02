import cv2
import imutils
import numpy as np

from cvlib.CvEnums import CvEnums


class CvHelper:

    @staticmethod
    def blend_mat(mat, mat2, alpha=1.0, beta=0.0, gamma=1.0):
        return cv2.addWeighted(src1=mat, alpha=alpha, src2=mat2, beta=beta, gamma=gamma)

    @staticmethod
    def erode(mat, kernel_shape=CvEnums.K_ELLIPSE, kernel_size=5, iterations=1):
        """
        https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.html
        It erodes away the boundaries of foreground object (Always try to keep foreground in white)
        :param iterations:
        :param kernel_size:
        :param kernel_shape:
        :param mat: greyscale image
        :return: eroded image
        """
        kernel = cv2.getStructuringElement(kernel_shape.value, (kernel_size, kernel_size))
        erosion = cv2.erode(mat, kernel, iterations=iterations)
        return erosion

    @staticmethod
    def morph(mat, gradient_type=CvEnums.MORPH_GRADIENT, kernel_shape=CvEnums.K_ELLIPSE, kernel_size=5):
        """
        Morphological transformations are some simple operations based on the image shape. It is normally performed
        on binarise images. It needs two inputs, one is our original image, second one is called structuring element or
        kernel which decides the nature of operation. Two basic morphological operators are Erosion and Dilation
        :param kernel_size:
        :param mat: binarise image
        :param gradient_type:
        :param kernel_shape:
        :return: morphed image
        """
        kernel = cv2.getStructuringElement(kernel_shape.value, (kernel_size, kernel_size))
        morph = cv2.morphologyEx(mat, gradient_type.value, kernel)
        return morph

    @staticmethod
    def equalise_hist(mat, by_tile=True, tile_size=None):
        """
        Equalise the brightness of an image
        :param tile_size:
        :param mat: greyscale image
        :param by_tile: if False it will take the whole image into account, but it creates noise.
        :return:
        """
        if by_tile:
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(tile_size, tile_size))
            return clahe.apply(mat)
        else:
            return cv2.equalizeHist(mat)

    @staticmethod
    def binarise(mat, thresh=127):
        """

        :param mat: greyscale image
        :param thresh: threshold amount
        :return: binarised image
        """
        ret, img_bin = cv2.threshold(mat, thresh, 255, 0)
        return img_bin

    @staticmethod
    def otsu_binary(mat, thresh=0):
        """
        When binarising an image, it might be best to first blur it
        :param mat: greyscale image
        :param thresh: threshold amount
        :return: binarised image
        """
        return cv2.threshold(mat, thresh, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]  # 1

    @staticmethod
    def dilate(mat, kernel_shape=CvEnums.K_RECTANGLE, kernel_size=5, iterations=1):
        """
        It is just opposite of erosion. Here, a pixel element is ‘1’ if atleast one pixel under the kernel is ‘1’. So
        it increases the white region in the image or size of foreground object increases. Normally, in cases like
        noise removal, erosion is followed by dilation. Because, erosion removes white noises, but it also shrinks
        our object. So we dilate it. Since noise is gone, they won’t come back, but our object area increases. It is
        also useful in joining broken parts of an object.
        :param kernel_shape:
        :param mat:
        :param kernel_size:
        :param iterations:
        :return:
        """
        kernel = cv2.getStructuringElement(kernel_shape.value, (kernel_size, kernel_size))
        # kernel = np.ones((kernel_size, kernel_size), np.uint8)
        dilate = cv2.dilate(mat, kernel, iterations=iterations)
        return dilate

    @staticmethod
    def sobel(mat, kernel_size=5):
        """
        https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_gradients/py_gradients.html
        :param mat: Needs to be source image
        :param kernel_size:
        :return:

        """
        sobely = cv2.Sobel(mat, cv2.CV_64F, 1, 1, ksize=kernel_size)
        abs_mat = np.absolute(sobely)
        return np.uint8(abs_mat)

    @staticmethod
    def laplacian(mat, kernel_size=11):
        """
        https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_imgproc/py_gradients/py_gradients.html
        :param mat: Needs to be source image
        :return:
        """

        laplacian = cv2.Laplacian(mat, cv2.CV_8U, ksize=kernel_size)
        abs_mat = np.absolute(laplacian)
        return np.uint8(abs_mat)

    @staticmethod
    def greyscale(mat):
        """
        Convert image to greyscale
        :param mat: accepts BGR image
        :return:
        """
        img_gray = cv2.cvtColor(mat, cv2.COLOR_BGR2GRAY)
        return img_gray

    @staticmethod
    def get_histogram(mat):
        """
        Get the brightness histogram of a greyscale image
        :param mat: greyscale image
        :return: Histogram
        """
        return cv2.calcHist(mat, [0, 1], None, [30, 32], [0, 256])

    @staticmethod
    def adaptive_thresholding(mat, thresh_type=CvEnums.THRESH_GAUSSIAN):
        """
        In the previous section, we used a global value as threshold value. But it may not be good in all the
        conditions where image has different lighting conditions in different areas. In that case, we go for adaptive
        thresholding. In this, the algorithm calculate the threshold for a small regions of the image. So we get
        different thresholds for different regions of the same image and it gives us better results for images with
        varying illumination.
        :param mat:
        :param thresh_type: CvEnums THRESH_GAUSSIAN or THRESH_MEAN
        :return:
        """
        t = cv2.adaptiveThreshold(mat, 255, thresh_type.value, cv2.THRESH_BINARY_INV, 11, 2)
        return t

    @staticmethod
    def canny_thresholding(mat_grey, lower_threshold=100, ratio=2):
        """
        https://docs.opencv.org/3.4/da/d5c/tutorial_canny_detector.html
        1. Filter out any noise. The Gaussian filter is used for this purpose
        2.
            a. Find the intensity gradient of the image
            b. Find the gradient strength and direction
        3. Non-maximum suppression is applied. This removes pixels that are not considered to be part of an edge. Hence, only thin lines (candidate edges) will remain
        4. Hysteresis: The final step. Canny does use two thresholds (upper and lower):
            a. If a pixel gradient is higher than the upper threshold, the pixel is accepted as an edge
            b. If a pixel gradient value is below the lower threshold, then it is rejected.
            c. If the pixel gradient is between the two thresholds, then it will be accepted only if it is connected to a pixel that is above the upper threshold.
        Canny recommended a upper:lower ratio between 2:1 and 3:1.
        :param mat_grey: Grey image
        :param ratio: ratio should either be 2 or 3
        :param lower_threshold: between 0 and 255
        :return:
        """
        blur = CvHelper.blur(mat_grey, kernel_size=3)
        upper_threshold = lower_threshold * ratio
        edges = cv2.Canny(blur, lower_threshold, upper_threshold)
        #mask = edges != 0
        #dst = mat_src * (mask[:, :, None].astype(mat_src.dtype))
        return edges

    @staticmethod
    def denoise(mat, intensity=2, search_window=21, block_size=7):
        """
        Denoise image
        :param mat: grayscale image
        :param intensity:
        :param search_window: usually 21
        :param block_size: usually 7
        :return: denoised image
        """
        return cv2.fastNlMeansDenoising(mat, intensity, search_window, block_size)

    @staticmethod
    def gaussian_blur(mat, kernel_size=5, sigma_x=0, sigma_y=0):
        """low_threshold
        https://docs.opencv.org/3.1.0/d4/d13/tutorial_py_filtering.html
        In this, instead of box filter, gaussian kernel is used. It is done with the function, cv2.GaussianBlur(). We
        should specify the width and height of kernel which should be positive and odd. We also should specify the
        standard deviation in X and Y direction, sigmaX and sigmaY respectively. If only sigmaX is specified,
        sigmaY is taken as same as sigmaX. If both are given as zeros, they are calculated from kernel size. Gaussian
        blurring is highly effective in removing gaussian noise from the image.
        :param mat:
        :param kernel_size:
        :param sigma_x:
        :param sigma_y:
        :return: blurred image
        """
        ksize = (kernel_size, kernel_size)
        blur = cv2.GaussianBlur(mat, ksize, sigma_x, sigma_y)
        return blur

    @staticmethod
    def box_filter_blur(mat, kernel_size=3, normalize=False):
        """
        https://docs.opencv.org/3.1.0/d4/d13/tutorial_py_filtering.html
        :param kernel_size:
        :param mat:
        :param normalize:
        :return:
        """
        ksize = (kernel_size, kernel_size)
        return cv2.boxFilter(mat, -1, ksize, normalize=normalize)

    @staticmethod
    def blur(mat, kernel_size=5):
        """
        https://docs.opencv.org/3.1.0/d4/d13/tutorial_py_filtering.html Blur image with average It simply takes the
        average of all the pixels under kernel area and replace the central element.
        :param mat:
        :param kernel_size:
        :return: Blurred image
        """
        kernel = (kernel_size, kernel_size)
        return cv2.blur(mat, kernel)

    @staticmethod
    def resize(mat, new_width=None, new_height=None, interpolation=CvEnums.MAT_INTER_AREA):
        """
        Only one side is needed. eg. width or height
        :param interpolation:
        :param mat:
        :param new_width:
        :param new_height:
        :return: resized image
        """
        if new_width and new_height is not None:
            return imutils.resize(mat, width=new_width, height=new_height, inter=interpolation.value)
        elif new_width is not None:
            return imutils.resize(mat, width=new_width, inter=interpolation.value)
        elif new_height is not None:
            return imutils.resize(mat, height=new_height, inter=interpolation.value)

        return mat

    @staticmethod
    def convert_img2bytes(mat):
        """
        Convert mat image to bytes for http transport
        :param mat:
        :return:
        """
        return cv2.imencode('.jpg', mat)[1].tostring()

    @staticmethod
    def rgb2bgr(mat):
        """
        Pretty much does what it says. Changes between colour scheme RGB -> BGR
        :param mat:
        :return: BGR image
        """
        return cv2.cvtColor(mat, cv2.COLOR_RGB2BGR)

    @staticmethod
    def bgr2rgb(mat):
        """
        Again does what it says. Changes between colour scheme BGR -> RGB
        :param mat:
        :return:
        """
        return cv2.cvtColor(mat, cv2.COLOR_BGR2RGB)

    @staticmethod
    def inverse(mat):
        """
        Inverses the colour scheme of a greyscale or binary image
        :param mat: greyscale image or binary.
        :return:
        """
        return cv2.bitwise_not(mat, mat)

    @staticmethod
    def bitwise_and(mat, mask=None):
        """
        https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_core/py_image_arithmetics/py_image_arithmetics.html
        :param mat:
        :param mask:
        :return:
        """
        if mask is not None:
            return cv2.bitwise_and(mat, mat, mask=mask)
        return cv2.bitwise_and(mat, mat)

    @staticmethod
    def bitwise_or(mat, mask):
        return np.bitwise_or(mat, mask)

    @staticmethod
    def display(window_name, mat, size=(None, None)):
        """
        Display mat or umat
        :param size: tuple (width, height) of image
        :param window_name:
        :param mat: umat is also supported
        :return: None
        """
        tmp = mat.copy()
        if any(size) is not None:
            width, height = size
            tmp = CvHelper.resize(tmp, new_width=width, new_height=height)
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.imshow(window_name, tmp)


    @staticmethod
    def destroy_window(window_name):
        """
        Destroy a window of specific name.
        :param window_name:
        :return: None
        """
        cv2.destroyWindow(window_name)

    @staticmethod
    def destroy_all_windows():
        """
        Destroy all windows being used.
        :return: None
        """
        cv2.destroyAllWindows()

    @staticmethod
    def draw_boxes(mat, arr_box_pnts, colour=CvEnums.COLOUR_GREEN, thickness=5):
        """
        Draw box of points on mat
        :param mat:
        :param arr_box_pnts:
        :param colour:
        :param thickness:
        :return: None
        """
        tmp = mat.copy()
        cv2.drawContours(tmp, arr_box_pnts, -1, colour.value, thickness)
        return tmp

    @staticmethod
    def draw_text(mat, text, position, colour=CvEnums.COLOUR_GREEN, thickness=5, scale=1):
        tmp = mat.copy()
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(tmp, text, position, font, scale, colour.value, thickness, cv2.LINE_AA)
        return tmp

    @staticmethod
    def get_umat(mat):
        """
        Convert to umat for OpenCL usage
        :param mat:
        :return: umat
        """
        return cv2.UMat(mat)

    @staticmethod
    def get_mat(umat):
        """
        Convert umat to mat
        :param umat:
        :return: mat
        """
        return umat.get()

    @staticmethod
    def mat_encode(mat, quality):
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        ret, img = cv2.imencode('.jpg', mat, encode_param)
        return img

    @staticmethod
    def mat_decode(image, flag=1):
        """
        Decode jpg or png to mat
        :param image:
        :param flag: 1 means colour. 0 greyscale
        :return: mat
        """
        return cv2.imdecode(image, flag)

    @staticmethod
    def write_mat(mat, path):
        cv2.imwrite(path, mat)

    @staticmethod
    def create_background_subtractor_knn(frame_amount, threshold, detect_shadows=True):
        """

        :param frame_amount:
        :param threshold:
        :param detect_shadows:
        :return:
        """
        return cv2.createBackgroundSubtractorKNN(frame_amount, threshold, detect_shadows)

    @staticmethod
    def copy_make_border(mat, sides=(0, 0, 0, 0), border_type=CvEnums.BORDER_CONSTANT, border_colour=CvEnums.COLOUR_WHITE):
        """
        https://docs.opencv.org/3.1.0/d3/df2/tutorial_py_basic_ops.html If you want to create a border around the
        image, something like a photo frame, you can use cv2.copyMakeBorder() function. But it has more applications
        for convolution operation, zero padding etc. This function takes following arguments:
        :param border_colour:
        :param border_type:
        :param sides: tuple(top, bottom, left, right)
        :param mat:
        :return:
        """
        top, bottom, left, right = sides
        return cv2.copyMakeBorder(src=mat, top=top, bottom=bottom, left=left, right=right, borderType=border_type.value, value=border_colour.value)

    @staticmethod
    def box_points(rectangles):
        box = cv2.boxPoints(rectangles)
        return np.int0(box)

    @staticmethod
    def moments(box_pnts):
        """
        https://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
        :param box_pnts: boxPoints
        :return:
        """
        return cv2.moments(box_pnts)

    @staticmethod
    def min_area_rect(contour):
        """
        https://docs.opencv.org/3.1.0/dd/d49/tutorial_py_contour_features.html
        :param contour:
        :return:
        """
        return cv2.minAreaRect(contour)

    @staticmethod
    def rotation_matrix_2D(center, angle, scale):
        """
        https://docs.opencv.org/3.4/da/d6e/tutorial_py_geometric_transformations.html
        :param scale:
        :param center:
        :param angle:
        :return:
        """
        return cv2.getRotationMatrix2D(center, angle, scale)

    @staticmethod
    def warp_affine(mat, input_array, out_size, flags=CvEnums.MAT_INTER_LINEAR, border_mode=CvEnums.BORDER_CONSTANT):
        """
        https://docs.opencv.org/3.4/da/d54/group__imgproc__transform.html#ga0203d9ee5fcd28d40dbc4a1ea4451983
        :param border_mode:
        :param mat:
        :param input_array:
        :param out_size:
        :param flags:
        :return:
        """
        return cv2.warpAffine(mat, input_array, out_size, flags=flags.value, borderMode=border_mode.value)

    @staticmethod
    def create_background_subtractor_mog2():
        return cv2.createBackgroundSubtractorMOG2(128, cv2.THRESH_BINARY, 1)

    @staticmethod
    def adjust_gamma(mat, gamma=1.0):
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(mat, table)