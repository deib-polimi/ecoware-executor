#!/usr/bin/env bash
echo color_prompt=yes >> /home/vagrant/.bashrc
echo "alias docker-set='docker exec -it docker-set docker'" >> /home/vagrant/.bashrc
echo "alias swarm='docker run -it --rm --privileged n43jl/swarm-set'" >> /home/vagrant/.bashrc

