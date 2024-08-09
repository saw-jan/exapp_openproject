#!/bin/bash

# start openproject
./docker/prod/entrypoint.sh ./docker/prod/supervisord &

# start exapp
echo "[INFO] Running exapp..."
python3 /exapp/lib/main.py
