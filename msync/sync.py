import sys
from pathlib import Path
from typing import Callable

from .db import PlaylistDB
from .ffstack import where as ffmpeg_location
from .utils import StyledThread
from .youtube.downloader import downloader
from .youtube.fetch import fetch_playlist, fetch_songs


def synchronize(playlist_id, db_path, music_dir):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = PlaylistDB(str(db_path))

    playlists_in_db = db.cur.execute(
        f"""
        SELECT 
            yt_playlist_id 
        FROM 
            {db.PLAYLIST_TABLE};
        """,
    ).fetchall()

    synced = (playlist_id,) in playlists_in_db

    music_dir = Path(music_dir)
    music_dir.mkdir(parents=True, exist_ok=True)

    playlist = run_async_func(func=fetch_playlist, args=([playlist_id],))[0]

    upstream_videos = run_async_func(func=fetch_songs, args=(playlist["videos"],))

    try:
        downloader(
            upstream_videos,
            playlist,
            str(music_dir.absolute()),
            ffmpeg_location(),
            {0: downloader_callback},
        )
    except KeyboardInterrupt:
        print()
        print("Exiting... (user interrupt)")
        sys.exit(130)


def downloader_callback(info):
    video_id = info["id"]


def run_async_func(func: Callable, args=None, kwargs=None):
    t = StyledThread(target=func, args=args, kwargs=kwargs)
    t.start()

    return t.styled_join(description="Fetching Playlists")


if __name__ == "__main__":
    DEMO_PLAYLIST = "PLrG0epTyFPvz4kUSXQC102CBhIl0-QHX9"
    synchronize(DEMO_PLAYLIST, "testing/testing.db", "testing/Music")
