#!/bin/bash

export APP_ID="openproject"
export APP_PORT="9030"
export APP_HOST="0.0.0.0"
export APP_SECRET="12345"
export APP_VERSION="1.0.0"
export AA_VERSION="2.8.0"
export NEXTCLOUD_URL="http://localhost/$NC_SUBFOLDER_PATH/index.php"
export OP_BACKEND_URL="http://localhost:8080/$NC_SUBFOLDER_PATH/index.php/apps/app_api/proxy/openproject"

python3.10 ex_app/lib/main.py
