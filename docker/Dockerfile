## TODO: Use build stages to create separate containers for building and running

# Base the image on Python 3 running on Alpine
FROM python:3.7.7-alpine

# Install base dependencies
RUN apk add --update --no-cache \
    bash \
    libffi \
    libxml2 \
    zlib \
    libxslt \
    libjpeg

# Install build dependencies
RUN apk add --update --no-cache --virtual build-dependencies \
    alpine-sdk \
    linux-headers \
    python-dev \
    libffi-dev \
    libxml2-dev \
    zlib-dev \
    libxslt-dev \
    jpeg-dev

# Switch to the image provided work directory
WORKDIR /usr/src/app

# Copy the installation script and install dependencies
COPY Install.py ./Install.py
RUN yes '' | python ./Install.py

# Remove build dependencies
RUN apk del build-dependencies

# Copy the rest of the application over
COPY . .

# Define default environment variables
ENV SETTINGS_DICT_PREFIX   ""
ENV SETTINGS_DICT_TOKEN    ""
ENV SETTINGS_DICT_WEATHER  ""
ENV SETTINGS_DICT_CURRENCY ""
ENV LAVALINK_HOST          "lavalink"
ENV LAVALINK_REGION        "us_central"

# Set the startup Python script
#CMD [ "python", "./WatchDog.py" ]
#CMD [ "python", "./Main.py" ]
CMD [ "docker/start.sh" ]
