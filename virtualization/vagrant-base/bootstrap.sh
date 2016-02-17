#!/usr/bin/env bash
sed -i '/^#force_color_prompt=yes/s/^#//' /home/vagrant/.bashrc
usermod -aG docker vagrant
    