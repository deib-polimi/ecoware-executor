FROM ubuntu:latest
MAINTAINER dsteblyuk@gmail.com

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -yq git python2.7 python-pip python-setuptools wget sqlite3
# TODO: delete
RUN pip install enum
# TODO: delete
RUN pip install protobuf
# TODO: delete
RUN pip install python-constraint
RUN wget https://pypi.python.org/packages/2.7/o/ortools/ortools-2.3393-py2.7-linux-x86_64.egg#md5=24197ea0616e7c61bd41d5b70f3e2e7d
RUN easy_install ortools-2.3393-py2.7-linux-x86_64.egg
RUN pip install awscli
RUN apt-get clean

WORKDIR /root
ADD run.sh /root/run.sh
CMD ["./run.sh"]
