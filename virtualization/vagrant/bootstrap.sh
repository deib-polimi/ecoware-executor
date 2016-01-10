#!/usr/bin/env bash
echo color_prompt=yes >> /home/vagrant/.bashrc
echo "alias docker-set='docker -H :2376 exec -it docker-set docker'" >> /home/vagrant/.bashrc
# echo "alias swarm='docker -H :2376 run -it --rm --privileged n43jl/swarm-set'" >> /home/vagrant/.bashrc
cp /vagrant/docker /etc/default/docker
service docker restart