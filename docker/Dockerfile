# Base the image on Python 3 running on Alpine
# FROM python:3.9.4-alpine3.13
FROM python:3.8.9-alpine3.13

# Install base dependencies
RUN apk add --update --no-cache \
    bash \
    git \
    openssh \
    ca-certificates \
    libffi \
    libxml2 \
    zlib \
    libxslt \
    libjpeg

# Install build dependencies
RUN apk add --update --no-cache --virtual build-dependencies \
    alpine-sdk \
    linux-headers \
    python3-dev \
    libffi-dev \
    libxml2-dev \
    zlib-dev \
    libxslt-dev \
    jpeg-dev

# Disable host key checking for git
RUN mkdir -p ~/.ssh && \
    echo -e "Host github.com\n\tStrictHostKeyChecking no\n" >> ~/.ssh/config

# Switch to the image provided work directory
WORKDIR /usr/src/app

# Copy the installation script and install dependencies
COPY Install.py ./Install.py
RUN yes '' | python ./Install.py

# Remove build dependencies
RUN apk del build-dependencies

# Copy the rest of the application over
COPY . .

# Create the data directory
RUN mkdir -p /data

# Define default environment variables
ENV SETTINGS_DICT_PREFIX               ""
ENV SETTINGS_DICT_TOKEN                ""
ENV SETTINGS_DICT_WEATHER              ""
ENV SETTINGS_DICT_CURRENCY             ""
ENV SETTINGS_DICT_SETTINGS_PATH        "/data/Settings.json"
ENV SETTINGS_DICT_SETTINGS_BACKUP_PATH "/data"
ENV SETTINGS_DICT_LAVALINK_HOST        "lavalink"
ENV SETTINGS_DICT_LAVALINK_REGION      "us_central"
ENV SETTINGS_DICT_LAVALINK_PASSWORD    "youshallnotpass"

# Expose volumes
VOLUME [ "/data" ]

# Set the startup Python script
CMD [ "docker/start.sh" ]
