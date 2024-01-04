import datetime
import os

import click

import msync.db as dba
import msync.sync as msc
from msync import PROG
from msync.utils import get_user_config_folder, get_user_data_folder


def get_default_paths():
    data_dir = get_user_data_folder()
    config_dir = get_user_config_folder()
    db_path = os.path.join(data_dir, dba.DB_FILE)
    storage_path = os.path.join(data_dir, "storage")
    music_path = os.path.expanduser("~/Music")
    return data_dir, config_dir, db_path, storage_path, music_path


@click.group()
def playlists():
    """Manage synchronising playlists"""


@playlists.command("list")
def show_playlists():
    db = dba.PlaylistDB(get_default_paths()[1])
    db.cur.execute(f"SELECT folder_name,update_time FROM {db.PLAYLIST_TABLE};")
    for i, k in enumerate(db.cur.fetchall(), start=1):
        date = datetime.datetime.fromisoformat(k[1])
        date_string = date.date().strftime("%d/%m/%Y")
        print(f"{i}. {k[0]}, synced on {date_string}")


@playlists.command("sync")
@click.argument("playlist_id")
def sync(playlist_id):
    msc.synchronize(playlist_id, *get_default_paths()[2:])
