#!/bin/bash
sudo apt update
sudo apt install python3-pip python3-opencv espeak-ng portaudio19-dev -y
pip3 install -r requirements.txt
