# Plateos

**A**utomatic **N**umber **P**late **R**ecognition using OpenCV and Tesseract for South African numberplates.

_Please note that this repository is unmaintained and has old code which is poorly documented._

## Background and Limitations

This started off as [a University project](https://github.com/Benehiko/ocr-core) which grew into a product which ended up being unused. The goal was to capture numberplates through cost efficient IP cameras at variable distances. This could range from a couple of meters 1m - 3m all the way to 10m - 15m away in variouse weather conditions. The goal was to get an accurate reading without a controlled area e.g. an undercover area with controlled light to capture the numberplate.

The extraction also had to occur without any human intervention, which would mean no triggers from the car driver (such as pressing a button) or third party. The project should also function with limited access to the internet (edge computing), should also be a low cost installation and should function throughout power outages.

Although some of these requirements were met, the main limitation of this project involves the accuracy against variable weather conditions and distance to the vehicles.

Requirements:

- [X] Automatic extraction all the time
- [X] Durable against power outages
- [X] Easy to add, replace and remove IP Cameras
- [X] Easy to expand to more edge devices
- [X] Limited internet access required
- [ ] Highly accurate in variable light/weather conditions and distance

## Harware used

- [Odroid xu4](https://www.hardkernel.com/shop/odroid-xu4-special-price/)
- [Reolink RLC-411ws](https://reolink.com/de/product/rlc-411ws/)

## Project architecture

This project assumes it has OpenCV, Python3 and Tesseract installed on the host machine. It also assumes that the system is Ubuntu. I don't think it should be a problem to run on Windows, but haven't tried it.

The project runs a couple of background tasks:

1. Managing IP Cameras
2. Extracting Numberplates from images
3. Saving and Uploading the data
4. A webserver displaying the data

Below are some steps that you can follow to install Teseract 4 and OpenCV 4.3.2.

### Tesseract 4.0

echo "Intalling Tesseract [4] ..."
echo $pass | sudo -S mkdir -p /usr/share/tesseract-ocr/4.00/tessdata/
wget https://github.com/tesseract-ocr/tessdata/raw/4.00/eng.traineddata
wget https://github.com/tesseract-ocr/tessdata/raw/3.04.00/osd.traineddata
echo $pass | sudo -S cp *.traineddata /usr/share/tesseract-ocr/4.00/tessdata/
echo $pass | sudo -S apt install --assume-yes tesseract-ocr libtesseract-dev libleptonica-dev

### OpenCv 4.3.2

echo "Installing OpenCV [4.3.2] ..."
wget -O opencv.tar.gz "https://github.com/opencv/opencv/archive/3.4.2.tar.gz"
wget -O opencv_contrib.tar.gz "https://github.com/opencv/opencv_contrib/archive/3.4.2.tar.gz"
tar xvf opencv.tar.gz
tar xvf opencv_contrib.tar.gz

### Install OpenCV system packages

echo $pass | sudo -S apt install --assume-yes build-essential cmake unzip pkg-config
echo $pass | sudo -S apt install --assume-yes libjpeg-dev libpng-dev libtiff-dev
echo $pass | sudo -S apt install --assume-yes libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
echo $pass | sudo -S apt install --assume-yes libxvidcore-dev libx264-dev
echo $pass | sudo -S apt install --assume-yes libatlas-base-dev gfortran  liblapacke-dev
sudo add-apt-repository "deb http://za.archive.ubuntu.com/ubuntu/ xenial main"
sudo apt install libjasper1 libjasper-dev

### Compile OpenCV && Install python

mkdir -p opencv-3.4.2/build/
cd opencv-3.4.2/build/
cmake -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=/usr/local DOPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-3.4.2/modules/ -DINSTALL_PYTHON_EXAMPLES=OFF -DBUILD_EXAMPLES=OFF -DBUILD_TESTS=OFF -DPYTHON_EXECUTABLE=/usr/bin/python3.6 -DENABLE_PRECOMPILED_HEADERS=OFF ..
make -j $(($(nproc) + 1))
sudo make install
sudo ldconfig
echo $pass | sudo -S mv /usr/local/lib/python3.6/dist-packages/cv2.cpython-36m-x86_64-linux-gnu.so /usr/local/lib/python3.6/dist-packages/cv2.so