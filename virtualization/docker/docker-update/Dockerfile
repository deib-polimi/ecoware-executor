FROM ubuntu:latest
MAINTAINER dsteblyuk@gmail.com

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq curl
RUN curl -fsSL https://test.docker.com/ | sh   # download v1.10_rc2
RUN apt-get clean