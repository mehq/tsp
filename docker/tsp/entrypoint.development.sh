#!/bin/bash

python -m pip install --upgrade pip
python -m pip install --requirement requirements.txt

exec "$@"
