import click

import msync.db as db
from msync import PROG


@click.group()
def playlists():
    """Manage synchronising playlists"""


@playlists.command("list")
def show_playlists():
    pass
