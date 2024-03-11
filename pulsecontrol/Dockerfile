# Buildplatform will the the platform the host is running on, not what was selected by `--platform`
#FROM --platform=$BUILDPLATFORM python:3.11-slim as base
FROM python:3.11-slim as base

#ARG DEBIAN_PACKAGE_ARCH=arm64
#ARG TRIPLE=arm64-unknown-linux-gnu
#ARG QEMU=qemu-aarch64
#ARG SYSROOT=/usr/aarch64-linux-gnu
#ARG CC=aarch64-linux-gnu-gcc
#ARG CXX=aarch64-linux-gnu-g++
#ARG AR=aarch64-linux-gnu-ar
#ARG STRIP=aarch64-linux-gnu-strip

ENV DEBIAN_FRONTEND="noninteractive" \
    # python envs
    PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    # PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # Fixes for cryptography builds
    CARGO_NET_GIT_FETCH_WITH_CLI=true \
    CRYPTOGRAPHY_DONT_BUILD_RUST=1 \
    \
    # poetry
    # https://python-poetry.org/docs/configuration/#using-environment-variables
    # make poetry install to this location
    POETRY_HOME="/opt/poetry" \
    # make poetry create the virtual environment in the project's root
    # it gets named `.venv`
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    # do not ask any interactive question
    POETRY_NO_INTERACTION=1 \
    BUILD_PATH="/build" \
    VENV_PATH="/build/.venv"


RUN apt-get update && apt-get install --assume-yes --no-install-recommends  \
    build-essential  \
    cmake  \
    meson  \
    ninja-build  \
    qemu-user-static  \
    git \
    libssl-dev \
    libffi-dev \
    python3-yaml python3-virtualenv python3-dev libpython3-dev python3-pkgconfig python3-pybind11 \
    pybind11-dev python3-jinja2 python3-ply libcap-dev python3-cryptography libjpeg-dev  \
    libatlas-base-dev python3-numpy


# rpi.gpio is only available on bookworm
# RUN apt-get install --assume-yes --no-install-recommends python3-rpi.gpio
RUN printf '[global]\nextra-index-url=https://www.piwheels.org/simple\n' > /etc/pip.conf

RUN pip install PyYAML jinja2 ply RPi.GPIO

RUN git clone https://github.com/raspberrypi/libcamera.git /libcamera

WORKDIR /libcamera
# one could either change `libdir` or change the PYTHONPATH after `ninja -C build install`
RUN meson setup build --buildtype=release -Dpipelines=rpi/vc4 -Dipas=rpi/vc4 -Dv4l2=true -Dgstreamer=disabled -Dtest=false -Dlc-compliance=disabled -Dcam=disabled -Dqcam=disabled -Ddocumentation=disabled -Dpycamera=enabled -Dlibdir=lib
RUN ninja -C build install

RUN git clone https://github.com/tomba/kmsxx.git /kmsxx
WORKDIR /kmsxx
RUN #meson wrap install fmt
RUN apt-get install --assume-yes --no-install-recommends libdrm-dev libfmt-dev
RUN #meson wrap install libdrm-common libdrm2 libdrm-dev libdrm
RUN meson setup build --buildtype=release -Dpykms=enabled -Dlibdir=lib
RUN ninja -C build

# ['', '/usr/local/lib/python311.zip', '/usr/local/lib/python3.11', '/usr/local/lib/python3.11/lib-dynload', '/usr/local/lib/python3.11/site-packages']
ENV PYTHONPATH=/kmsxx/build/py

# So libcamera.so.0.1 can be ound
RUN ldconfig

# Picamera and opencv dependencies
RUN apt-get install --assume-yes --no-install-recommends  \
    libtiff6  \
    libopenjp2-7 \
    libxcb1 \
    libpng16-16


WORKDIR /usr/src/app

# Install Poetry
RUN #which python3
RUN #python3 --version

# This is a hack for cryprography
#ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN #python3 -m pip install poetry
# prepend poetry, venv and pipx to path
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:/root/.local/bin:$PATH"

# RUN python3 -m venv $VENV_PATH
# RUN python3 -m pip install --upgrade pip
RUN #which python3
RUN #python3 --version
# RUN python3 -m pip install pipx && \
#    python3 -m pipx ensurepath

FROM base as build

#RUN pipx install poetry
RUN pip install poetry
RUN poetry --version

WORKDIR $BUILD_PATH

# NOTE: This only works when installing with pip: https://github.com/python-poetry/poetry/issues/6035
# Use system packages, so libcamera can be used
# RUN poetry config virtualenvs.options.system-site-packages true
#RUN poetry export > requirements.txt
#RUN poetry run pip install -r requirements.txt
RUN poetry config installer.max-workers 10

# Use system python
RUN poetry config virtualenvs.create false

RUN poetry config --list

#RUN --mount=target=/root/.cache/pypoetry,type=cache,sharing=locked  \
#    --mount=target=/root/.cache/pip,type=cache,sharing=locked  \
#    poetry run pip install /wheels

# RUN --mount=target=/root/.cache/pypoetry,type=cache,sharing=locked \
#    --mount=target=/root/.cache/pip,type=cache,sharing=locked  \
#    poetry install --no-interaction -vvv


#COPY poetry.lock poetry.lock
COPY pyproject.toml pyproject.toml
RUN poetry env info
#COPY wheels wheels

RUN #poetry lock
# Done to avoid re-istalling already installed systme packages
RUN poetry export --without-hashes --with dev -f requirements.txt -o requirements.txt
RUN pip install -r requirements.txt
RUN #poetry install --no-interaction -vvv

# Install additional dependencies
RUN apt-get update && apt-get install --assume-yes  \
    ffmpeg \
    libgtk-3-0

#FROM base as runtime

#COPY --from=build $BUILD_PATH $BUILD_PATH
COPY ./pulsecontrol /app/pulsecontrol
WORKDIR /app

#CMD [ "hypercorn", "-b", "0.0.0.0:5000", "snapper.main:app" ]
CMD [ "gunicorn", "-w", "1", "-b", "0.0.0.0:5000", "pulsecontrol.main:app"]

FROM build as charm

CMD ["python3"]
