FROM golang:latest
MAINTAINER dsteblyuk@gmail.RUN

WORKDIR $GOPATH/src/github.com/docker/
RUN go get github.com/tools/godep
RUN git clone -b add_set https://github.com/affo/swarm
RUN cd swarm && godep go install

ENTRYPOINT swarm
