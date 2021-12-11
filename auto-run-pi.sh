#!/bin/sh
cd /home/pi/git/BakpdlBot
git pull
source venv/bin/activate
if [[ "$VIRTUAL_ENV" != "" ]]
then
    pip install -r requirements_dev.txt
    python bakpdlbot/discord/discord_bot.py
fi
