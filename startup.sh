#!/bin/sh
SCRIPT_DIR=$(dirname "$(realpath "$0")")

bash $SCRIPT_DIR/post-init.sh

jupyter server --ServerApp.ip=0.0.0.0 --ServerApp.port=8888 --ServerApp.base_url=$RENKU_BASE_URL_PATH --ServerApp.token="" --ServerApp.password="" --ServerApp.allow_remote_access=true --ContentsManager.allow_hidden=true --ServerApp.allow_origin=* --ServerApp.root_dir="/home/jovyan/work"

