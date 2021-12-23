#!/bin/sh
cd /home/pi/git/BakpdlBot
git pull
source venv/bin/activate
if [[ "$VIRTUAL_ENV" != "" ]]
then
    pip install -e .
    bakpdlbot
fi
