#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar FFmpeg
apt-get update
apt-get install -y ffmpeg

pip install -r requirements.txt