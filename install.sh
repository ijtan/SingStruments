#!/bin/bash
sudo apt install timidity python3.8 libatlas-base-dev -y
python3.8 -m pip install pipenv wheel
python3.8 -m pipenv install uvicorn wheel fastapi "tensorflow>=2.0.0" tensorflow_hub aiofiles scipy pydub music21 jinja2 python-multipart
