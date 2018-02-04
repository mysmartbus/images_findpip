# Original Version: https://github.com/janza/docker-python3-opencv
#
# Modified by mysmartbus (https://github.com/mysmartbus) for use on the Raspberry Pi 2 & 3.
#
# Last Modified: 2018-01-12 2144
#
# Build time on a Raspberry Pi 2 is approximately 2hrs 25m.

FROM python:3.6

LABEL maintainer="mysmartbus (https://github.com/mysmartbus)"

RUN apt-get update && \
        apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        libavformat-dev \
        libjasper-dev \
        libjpeg-dev \
        liblapack3 \
        libpng-dev \
        libswscale-dev \
        libtiff-dev \
        pkg-config \
        # python3-pil \ Install via requirements.txt \
        unzip \
        yasm \
        wget \
        # \
        # Scipy and dependencies \
        python3-scipy \
        libatlas-dev \
        libblas-dev \
        python3-numpy \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY . /

RUN pip install -r /requirements.txt

ENV OPENCV_VERSION="3.4.0"

# Notes for cmake:
#   -DENABLE_NEON=ON generates compiler error "Required baseline optimization is not supported: NEON"
#   -DENABLE_AVX=ON generates compiler warning "Option ENABLE_AVX='ON' is deprecated and should not be used anymore"
#
#   Nvidia related:
#   -DWITH_CUDA=OFF
#   -DWITH_CUFFT=OFF
#   -DWITH_CUBLAS=OFF
#   -DWITH_NVCUVID=OFF
#
#   The /opencv-${OPENCV_VERSION}/cmake_binary directory is where cmake will put the generated Makefiles, project
#   files, object files and output binaries
#
#   The .. on the PYTHON_PACKAGES_PATH is required so that cmake can find the opencv source code in /opencv-${OPENCV_VERSION}
#
#   Changed these lines to use python3 instead of python3.6
#   -DCMAKE_INSTALL_PREFIX=$(python3.6 -c "import sys; print(sys.prefix)") \
#   -DPYTHON3_EXECUTABLE=$(which python3.6) \
#   -DPYTHON_INCLUDE_DIR=$(python3.6 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
#   -DPYTHON_PACKAGES_PATH=$(python3.6 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") .. \
#
# https://github.com/opencv/opencv/blob/master/CMakeLists.txt
#
# Install on linx from source: https://docs.opencv.org/trunk/d7/d9f/tutorial_linux_install.html
#
RUN wget https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip \
&& unzip ${OPENCV_VERSION}.zip \
&& mkdir /opencv-${OPENCV_VERSION}/cmake_binary \
&& cd /opencv-${OPENCV_VERSION}/cmake_binary \
&& cmake -DBUILD_TIFF=ON \
  -DBUILD_opencv_java=OFF \
  -DBUILD_TESTS=OFF \
  -DBUILD_PERF_TESTS=OFF \
  -DENABLE_VFPV3=ON \
  -DWITH_1394=OFF \
  -DWITH_CUDA=OFF \
  -DWITH_CUFFT=OFF \
  -DWITH_CUBLAS=OFF \
  -DWITH_EIGEN=ON \
  -DWITH_IPP=OFF \
  -DWITH_NVCUVID=OFF \
  -DWITH_OPENGL=ON \
  -DWITH_OPENCL=ON \
  -DWITH_V4L=ON \
  -DCMAKE_BUILD_TYPE=RELEASE \
  -DCMAKE_INSTALL_PREFIX=$(python3.6 -c "import sys; print(sys.prefix)") \
  -DPYTHON3_EXECUTABLE=$(which python3.6) \
  -DPYTHON_INCLUDE_DIR=$(python3.6 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
  -DPYTHON_PACKAGES_PATH=$(python3.6 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
  -DPYTHON3_NUMPY_INCLUDE_DIRS=/usr/lib/python3/dist-packages/numpy/core/include/ .. \
&& make install \
&& rm /${OPENCV_VERSION}.zip \
&& rm -r /opencv-${OPENCV_VERSION}

EXPOSE 6003

# The '-u' tells python to run in unbuffered mode.
# Unbuffered mode allows you to use 'docker attach <container_name>' and see the debug
# messages without having to stop the container.
# More info: https://docs.python.org/3/using/cmdline.html#cmdoption-u
CMD [ "python", "-u", "/images_findpip_server.py" ]
