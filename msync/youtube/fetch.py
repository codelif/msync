"""
src/fetch.py - Fetch Playlist and Video Information with YouTubeDL.

Copyright (C) 2022  Harsh Sharma  <goharsh007@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

import yt_dlp
from youtube_title_parse import get_artist_title as extract
from yt_dlp import YoutubeDL


def fetch_songs(videos_generator) -> list[dict[str, str]]:
    # collecting relevant information in a dictionary and appending it in the playlist list
    playlist = []
    ids = []
    for i in videos_generator:
        if i["id"] in ids:
            continue
        if i["title"].lower() in [
            "private video",
            "deleted video",
        ]:  # Check for private/deleted videos
            continue
        try:
            # Parse the title to extract only the artist and title.
            artist, title = extract(i["title"])
        except TypeError:
            # Fallback if youtube_title_parse is not able to parse a title.
            artist, title = (i["channel"], i["title"])

        video = {
            "id": i["id"],
            "title": title.replace("/", "-"),  # special case
            "artist": artist.replace(" - Topic", ""),  # special case
        }

        ids.append(i["id"])
        playlist.append(video)

    return playlist


class Logger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass


def fetch_playlist(playlist_IDs: list) -> list[dict]:
    response = []
    LINK = "https://www.youtube.com/playlist?list=%s"
    with YoutubeDL(params={"quiet": True, "logger": Logger()}) as dl:
        for pid in playlist_IDs:
            try:
                info = dl.extract_info(LINK % pid, process=False)
                response.append(info)
            except yt_dlp.utils.DownloadError as e:
                print(e)

    # collecting relevant information in a dictionary and appending it in the playlist list
    playlists = []
    for i in response:
        playlist = {
            "id": i["id"],
            "title": i["title"],
            "count": i["playlist_count"],
            "videos": i["entries"],
        }
        playlists.append(playlist)

    return playlists
