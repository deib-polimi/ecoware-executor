#!/usr/bin/env bash
echo color_prompt=yes >> /home/vagrant/.bashrc
curl -fsSL https://test.docker.com/ | sh   # download v1.10_rc2
usermod -aG docker vagrant
docker pull nginx
docker pull httpd
echo 'DOCKER_OPTS="-H tcp://0.0.0.0:2376"' >> /etc/default/docker
service docker restart
echo "alias dock='docker -H :2376'" >> /home/vagrant/.bashrc
