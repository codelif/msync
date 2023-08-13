import sqlite3
import datetime
import os
from uuid import uuid4 as gen_uuid


DB_FILE = "synchronisation_data.db"


class PlaylistDB:
    """
    PlaylistDB class.

    Contains methods to (add, update or lookup) playlists or songs.

    """

    PLAYLIST_TABLE = "playlists"
    SONGS_TABLE = "songs"

    def __init__(self, db_path: str) -> None:
        """Creates a database (if it doesn't exist), connects to it and sets up playlist and songs tables.

        Args:
            db_path (str): Database file.
        """
        self.conn = sqlite3.connect(db_path)
        self.cur = self.conn.cursor()

        self.__setup_database()

    def __del__(self) -> None:
        self.cur.close()
        self.conn.close()

    def __generate_id(self, check_collision: bool = True) -> str:
        UUID_EXTRACT = f"""
            SELECT 
                playlist_id 
            FROM 
                {self.PLAYLIST_TABLE} 
            UNION 
            SELECT 
                song_id 
            FROM 
                {self.SONGS_TABLE};
        """

        uuids = []
        if check_collision:
            uuids = self.cur.execute(UUID_EXTRACT).fetchall()

        uuid = str(gen_uuid())

        # Collision check Just in case, yk :)
        while (uuid,) in uuids:
            uuid = str(gen_uuid())

        return uuid

    def __setup_database(self, commit=True) -> None:
        CREATE_PLAYLIST_TABLE = f"""CREATE TABLE IF NOT EXISTS {self.PLAYLIST_TABLE} (
                enabled integer NOT NULL,
                playlist_id text NOT NULL UNIQUE,
                yt_playlist_id text,
                folder_path NOT NULL,
                folder_name text,
                update_time text
            );"""

        CREATE_SONGS_TABLE = f"""CREATE TABLE IF NOT EXISTS {self.SONGS_TABLE} (
                song_id text NOT NULL UNIQUE,
                file_path text NOT NULL,
                yt_song_id text,
                playlists text
            );"""

        self.cur.execute(CREATE_PLAYLIST_TABLE)
        self.cur.execute(CREATE_SONGS_TABLE)

        if commit:
            self.conn.commit()

    def create_playlist_entry(
        self, enabled, yt_playlist, folder_path, folder_name, commit=True
    ) -> str:
        INSERT_PLAYLIST = (
            f"""INSERT INTO {self.PLAYLIST_TABLE} VALUES (?, ?, ?, ?, ?, ?)"""
        )

        update_time = datetime.datetime.now().isoformat()
        playlist_id = self.__generate_id()

        self.cur.execute(
            INSERT_PLAYLIST,
            (enabled, playlist_id, yt_playlist, folder_path, folder_name, update_time),
        )

        if commit:
            self.conn.commit()

        return playlist_id

    def create_song_entry(self, file_path, yt_song_id, playlists, commit=True) -> str:
        INSERT_SONG = f"""INSERT INTO {self.SONGS_TABLE} VALUES (?, ?, ?, ?)"""

        song_id = self.__generate_id()
        file_path = os.path.abspath(file_path)
        playlists_str = ",".join(playlists)

        self.cur.execute(INSERT_SONG, (song_id, file_path, yt_song_id, playlists_str))

        if commit:
            self.conn.commit()

        return song_id

    def add_song_playlist(self, song_id, playlist_id, commit=True):
        FETCH_PLAYLISTS = f"""
            SELECT 
                playlists 
            FROM 
                {self.SONGS_TABLE} 
            WHERE 
                song_id = ? ;
        """

        UPDATE_PLAYLIST = f"""
            UPDATE 
                {self.SONGS_TABLE}
            SET 
                playlists = ?
            WHERE
                song_id = ? ;
        """

        playlists: list = (
            self.cur.execute(FETCH_PLAYLISTS, (song_id,)).fetchone()[0].split(",")
        )

        if playlist_id in playlists:
            return

        playlists.append(playlist_id)

        playlists_str = ",".join(playlists)
        self.cur.execute(UPDATE_PLAYLIST, (playlists_str, song_id))

        if commit:
            self.conn.commit()

    def remove_song_playlist(self, song_id, playlist_id, commit=True):
        FETCH_PLAYLISTS = f"""
            SELECT 
                playlists 
            FROM 
                {self.SONGS_TABLE} 
            WHERE 
                song_id = ? ;
        """

        UPDATE_PLAYLIST = f"""
            UPDATE 
                {self.SONGS_TABLE}
            SET 
                playlists = ?
            WHERE
                song_id = ? ;
        """

        playlists: list = (
            self.cur.execute(FETCH_PLAYLISTS, (song_id,)).fetchone()[0].split(",")
        )

        if playlist_id not in playlists:
            return

        playlists.remove(playlist_id)

        playlists_str = ",".join(playlists)
        self.cur.execute(UPDATE_PLAYLIST, (playlists_str, song_id))

        if commit:
            self.conn.commit()
