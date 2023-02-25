#!/usr/bin/env bash

echo "STATUS: RUNNING POST CLONE..."

PKG_NAME="dialogflow-utils"
PKG_BASE="$(pwd)"

ROS_ENV="/opt/ros/noetic/setup.bash"
source ${ROS_ENV}

roscd

CATKIN_ENV="$(pwd)/setup.bash"
source ${CATKIN_ENV}

cd "${PKG_BASE}"

PYTHON3="$(which python3)"
VENV_BASE="venv"
VENV_PYTHON="${VENV_BASE}/bin/python"

${PYTHON3} -m venv ${VENV_BASE}

source "${VENV_BASE}/bin/activate"

pip install -U pip
pip install -r requirements.txt

spacy download en_core_web_sm

deactivate

echo "STATUS: POST CLONE SUCCESSFUL"