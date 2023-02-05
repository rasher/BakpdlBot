"""Console script for bakpdlbot."""
import logging
import os
import sys

import click
from dotenv import load_dotenv

from .discord_bot import bot


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(debug, args=None):
    """Console script for bakpdlbot."""
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')
    bot.run(TOKEN)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
