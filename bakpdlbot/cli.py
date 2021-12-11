"""Console script for bakpdlbot."""
import sys
import click


@click.command()
def main(args=None):
    """Console script for bakpdlbot."""
    click.echo("Replace this message by putting your code into "
               "bakpdlbot.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
