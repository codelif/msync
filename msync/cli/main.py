import click

from msync import PROG
from msync.cli.ffmpeg import ffmpeg
from msync.cli.playlists import playlists


@click.group(PROG)
def cli():
    """Music Manager for *nix systems."""


cli.add_command(ffmpeg)
cli.add_command(playlists)


@cli.group()
def songs():
    pass


@songs.command()
def list():
    pass
