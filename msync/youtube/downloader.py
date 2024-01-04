"""
src/downloader.py - Downloads and Converts upstream YouTube media.

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

from __future__ import unicode_literals

import tempfile
from typing import Any, Callable

import yt_dlp as youtube_dl
from mutagen.easymp4 import EasyMP4
from tqdm import tqdm


class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        # print(msg)
        pass


def update_metadata(media_file: str, title: str, artist: str):
    audio = EasyMP4(media_file)
    audio["title"] = title
    audio["artist"] = artist
    audio.save()


class ProgressHook:
    def __init__(self) -> None:
        self.bar = tqdm(
            unit="B",
            unit_divisor=1024,
            unit_scale=True,
            position=0,
            leave=False,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ",
        )
        self.bar.clear()
        self.started = False
        self.last_down = 0

    def hook(self, d):
        if not self.started:
            self.bar.total = float(d["total_bytes"])
            self.bar.refresh()
            self.started = True
        # print(d)
        if d["status"] == "downloading":
            downloaded_bytes_delta = float(d["downloaded_bytes"]) - self.last_down
            self.bar.update(downloaded_bytes_delta)
            self.last_down = float(d["downloaded_bytes"])

        if d["status"] == "finished":
            self.bar.clear()

    def update(self, video):
        desc = f"{video['title'] if len(video['title']) < 25 else video['title'][:25]+'...'}"
        self.bar.set_description(desc)
        self.bar.reset()
        self.last_down = 0
        self.started = False


def gen_options(
    playlist, output_folder, tmpdir, video, ffmpeg_string, prog: ProgressHook
):
    prog.update(video)

    ydl_opts = {
        "writethumbnail": True,
        "format": "m4a/bestaudio/best",
        "outtmpl": f'{video["artist"]} - {video["title"]}.%(ext)s',
        "paths": {"temp": tmpdir, "home": output_folder},
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "m4a",
            },
            {"key": "FFmpegMetadata", "add_metadata": "True"},
            {"key": "EmbedThumbnail", "already_have_thumbnail": False},
        ],
        "logger": MyLogger(),
        "progress_hooks": [prog.hook],
    }

    if ffmpeg_string:
        ydl_opts["ffmpeg_location"] = ffmpeg_string

    return ydl_opts


def downloader(
    videos,
    playlist,
    output_folder,
    ffmpeg_string,
    callback: dict[str, Any],
):
    prog = ProgressHook()
    print(f"Downloading '{playlist['title']}'...")
    with tempfile.TemporaryDirectory() as tmpdir:
        for video in tqdm(
            videos,
            desc=playlist["title"],
            position=1,
            leave=True,
            colour="GREEN",
            bar_format="{desc}: {n_fmt}/{total_fmt}|{bar}|",
        ):
            filename = f'{output_folder}/{video["artist"]} - {video["title"]}.m4a'
            ydl_opts = gen_options(
                playlist, output_folder, tmpdir, video, ffmpeg_string, prog
            )
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl.download([video["id"]])
                    update_metadata(
                        filename, video["title"], video["artist"]
                    )  # update with more refined metadata
                    info = {
                        "id": video["id"],
                        "title": video["title"],
                        "artist": video["artist"],
                        "file": filename,
                        "folder": output_folder,
                    }

                    callback_kwargs = {
                        callback["info_kwarg"]: info,
                        **callback["kwargs"],
                    }
                    callback["target"](**callback_kwargs)

                except (
                    youtube_dl.utils.ExtractorError,
                    youtube_dl.utils.DownloadError,
                ):
                    print(
                        "Error occured while trying to download '%s'. Skipping..."
                        % f"https://youtu.be/{video['id']}"
                    )
                    continue
