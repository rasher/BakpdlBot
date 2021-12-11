#!/bin/sh
cd /home/pi/git/BakpdlBot
git pull
source venv/bin/activate
pip install -r requirements_dev.txt


python bakpdlbot/discord/discord_bot.py
