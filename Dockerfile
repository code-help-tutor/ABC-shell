FROM python:3.8-buster

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get -y install --no-install-recommends apt-utils dialog 2>&1 \
    && apt-get -y install git procps lsb-release 	libxml2-utils \
    && apt-get autoremove -y \
    && apt-get clean -y

RUN /usr/local/bin/python -m pip install --upgrade pip

COPY . /abc

RUN chmod u+x /abc/sh
RUN chmod u+x /abc/tools/test
RUN chmod u+x /abc/tools/coverage
RUN chmod u+x /abc/tools/analysis

RUN cd /abc && python -m pip install -r requirements.txt

ENV DEBIAN_FRONTEND=

EXPOSE 8000

