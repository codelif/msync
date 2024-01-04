import os

import click

from msync import PROG
from msync.cli.ffmpeg import ffmpeg
from msync.cli.playlists import get_default_paths, playlists
from msync.sync import synchronize
from msync.utils import get_user_config_folder


@click.group(PROG)
def cli():
    """Music Manager for *nix systems."""


@click.command("sync")
def sync():
    "Synchronise playlists in sync.lst"
    pl = []
    paths = get_default_paths()
    try:
        with open(os.path.join(paths[1], "sync.lst"), "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue
                elif not line:
                    continue

                com = line.rfind(" #")
                if com != -1:
                    line = line[:com].strip()
                pl.append(line)
    except FileNotFoundError:
        pl = []

    if len(pl) == 0:
        print("Sync List is empty!")
        return 1

    print("Synchronising %d playlist(s):\n" % len(pl))

    for p in pl:
        synchronize(p, *paths[2:])


cli.add_command(ffmpeg)
cli.add_command(playlists)
cli.add_command(sync)
