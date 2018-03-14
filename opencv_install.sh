#!/bin/bash

# Installs python 3.5 and then builds opencv with support for python 3.5

# The cmake line has been partially customized for a computer with the following hardware:
#   - Intel Pentium 4 CPU 3.20GHz
#   - Nvidia GeForce 6800 XT
#
# For a list of OpenCV cmake options and what they are for, go to https://github.com/opencv/opencv/blob/master/CMakeLists.txt
# The option names and descriptions start around line 200.

# Created: 2018-01-??
# Modified: 2018-03-14

OPENCV_VERSION="3.4.0"

# Install Python3.5
sudo apt-get install python3.5

# Packages required to build and use opencv
sudo apt-get install build-essential cmake git libavformat-dev libjasper-dev libjpeg-dev liblapack3 libpng-dev libswscale-dev libtiff-dev pkg-config python3-pil unzip yasm wget python3-scipy libatlas-dev libblas-dev python3-numpy

# Go to your home folder
cd ~

# Download and extract OpenCV
wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip
unzip ./${OPENCV_VERSION}.zip

# Create the directory used to store the compiled program
mkdir ./opencv-${OPENCV_VERSION}/cmake_binary

cd ./opencv-${OPENCV_VERSION}/cmake_binary

# Begin the build of OpenCV
#
# The .. at the end of this line is required so that cmake can find the opencv source code in /opencv-${OPENCV_VERSION}
cmake -DBUILD_TIFF=ON -DBUILD_opencv_java=OFF -DBUILD_TESTS=OFF -DBUILD_PERF_TESTS=OFF -DENABLE_VFPV3=ON -DWITH_1394=OFF -DWITH_CUDA=ON -DWITH_CUFFT=ON -DWITH_CUBLAS=ON -DWITH_EIGEN=ON -DWITH_IPP=OFF -DWITH_NVCUVID=ON -DWITH_OPENGL=ON -DWITH_OPENCL=ON -DWITH_V4L=ON -DCMAKE_BUILD_TYPE=RELEASE -DCMAKE_INSTALL_PREFIX=$(python3.5 -c "import sys; print(sys.prefix)") -DPYTHON3_EXECUTABLE=$(which python3.5) -DPYTHON_INCLUDE_DIR=$(python3.5 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") -DPYTHON_PACKAGES_PATH=$(python3.5 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") -DPYTHON3_NUMPY_INCLUDE_DIRS=/usr/lib/python3/dist-packages/numpy/core/include/ ..

# Install OpenCV
sudo make install
