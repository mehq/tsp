#!/bin/bash

python -m pip install --upgrade pip
pip install --requirement requirements.txt

exec "$@"
