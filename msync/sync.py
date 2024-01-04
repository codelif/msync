import sys
from pathlib import Path
from typing import Callable

from .db import PlaylistDB
from .ffstack import where as ffmpeg_location
from .utils import StyledThread
from .youtube.downloader import downloader
from .youtube.fetch import fetch_playlist, fetch_songs


def synchronize(yt_playlist_id, db_path, storage_dir, music_dir):
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    music_dir = Path(music_dir)
    music_dir.mkdir(parents=True, exist_ok=True)
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    db = PlaylistDB(str(db_path))

    playlists_in_db = db.cur.execute(
        f"""
        SELECT 
            yt_playlist_id
        FROM 
             {db.PLAYLIST_TABLE}; 
        """,
    ).fetchall()

    synced = (yt_playlist_id,) in playlists_in_db
    playlist = run_async_func(func=fetch_playlist, args=([yt_playlist_id],))[0]
    upstream_videos = fetch_songs(playlist["videos"])
    # print(len(upstream_videos))
    if not synced:
        db_playlist_id = db.create_playlist_entry(
            True, yt_playlist_id, str(music_dir.absolute()), playlist["title"]
        )
    else:
        db_playlist_id = db.cur.execute(
            f"""
                SELECT
                    playlist_id
                FROM
                    {db.PLAYLIST_TABLE}
                WHERE
                    yt_playlist_id = ?
            """,
            (yt_playlist_id,),
        ).fetchone()[0]

    songs_in_db = db.cur.execute(
        f"""
            SELECT
                yt_song_id, song_id, playlists
            FROM
                {db.SONGS_TABLE}
        """,
    ).fetchall()

    music_dir.joinpath(playlist["title"]).mkdir(parents=True, exist_ok=True)

    downable_videos = []
    downed_videos = []
    for i in upstream_videos:
        downed = False
        song_playlists = []
        song_uuid = ""
        for yt_song_id, sid, song_p in songs_in_db:
            if yt_song_id == i["id"]:
                downed = True
                song_playlists = song_p.split(",")
                song_uuid = sid
                break
        if downed:
            downed_videos.append(i)
            if db_playlist_id not in song_playlists:
                db.add_song_playlist(song_uuid, db_playlist_id)
        else:
            downable_videos.append(i)

    try:
        callback = {
            "target": downloader_callback,
            "kwargs": {"db": db, "playlist_uuid": db_playlist_id},
            "info_kwarg": "info",
        }

        if len(downable_videos) != 0:
            downloader(
                downable_videos,
                playlist,
                str(storage_dir.absolute()),
                ffmpeg_location(),
                callback,
            )

        for i in upstream_videos:
            try:
                loc = db.cur.execute(
                    f"""
                        SELECT
                            file_path
                        FROM
                            {db.SONGS_TABLE}
                        WHERE
                            yt_song_id = ?
                    """,
                    (i["id"],),
                ).fetchone()[0]
            except TypeError:
                continue
            storage_song_path = Path(loc)
            symlink_path = music_dir.joinpath(playlist["title"], storage_song_path.name)
            if symlink_path.exists():
                continue

            symlink_path.symlink_to(storage_song_path)

        print("\033[1;32m✔\033[0m '%s' Synced!" % playlist["title"])

    except KeyboardInterrupt:
        print()
        print("Exiting... (user interrupt)")
        sys.exit(130)


def downloader_callback(info: dict, db: PlaylistDB, playlist_uuid: str):
    songs_in_db = db.cur.execute(
        f"""
            SELECT
                yt_song_id
            FROM
                {db.SONGS_TABLE}
        """,
    ).fetchall()
    if (info["id"],) not in songs_in_db:
        db.create_song_entry(info["file"], info["id"], (playlist_uuid,))


def run_async_func(func: Callable, args=None, kwargs=None):
    t = StyledThread(target=func, args=args, kwargs=kwargs)
    t.start()

    return t.styled_join(description="Fetching Playlists")
