# fmt: off

# testing self mutable Progress Hook for automatic detection

import yt_dlp
from src.sync import run_async_func
from src.youtube.fetch import fetch_playlist, fetch_songs
import sys
from tqdm import tqdm

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)


    # sys.exit(1)
    
class ProgressHook:
    def __init__(self, videos) -> None:
        self.videos_index = videos
        self.bar = tqdm(
            unit="B",
            unit_divisor=1024,
            unit_scale=True,
            position=0,
            leave=False,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} ",
        )
        self.bar.clear()
        self.current = None

    def hook(self, d):
        if self.current != d["info_dict"]["display_id"]:
            self.current = d["info_dict"]["display_id"]
            self.update(self.videos_index[self.current], float(d["total_bytes_estimate"]))
            self.bar.refresh()
        # print(d)
        if d["status"] == "downloading":
            self.bar.update(float(d["downloaded_bytes"]))

        # if d["status"] == "finished":
        #     self.bar.clear()

    def update(self, video, total):
        desc = f"{video['title'] if len(video['title']) < 25 else video['title'][:25]+'...'}"
        self.bar.set_description(desc)
        self.bar.reset(total=total)

# current = None
# def hook(d:dict):
#     global current
#     if d["filename"] != current:
#         current = d["filename"]
#         from pprint import pprint
#         d.pop('info_dict')
#         pprint(d)
    

# URLS = ["https://www.youtube.com/watch?v=1puGzGe_mfU"]
DEMO_PLAYLIST = "PLrG0epTyFPvz4kUSXQC102CBhIl0-QHX9"



playlist = run_async_func(fetch_playlist, ([DEMO_PLAYLIST,],),)[0]

videos = fetch_songs(playlist['videos'])
video_urls = [i['id'] for i in videos]
video_index = {i['id']:{'title':i['title'], 'artist': i['artist']} for i in videos}
prog = ProgressHook(video_index)
# print(video_urls)

ydl_opts = {
    "writethumbnail": True,
    "format": "m4a/bestaudio/best",
    "ffmpeg_location": "/Users/harsh/Library/Application Support/msync/ffmpeg_builds",
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    "postprocessors": [
        {  # Extract audio using ffmpeg
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
        },
            {"key": "FFmpegMetadata", "add_metadata": "True"},
            {"key": "EmbedThumbnail", "already_have_thumbnail": False},
    ],
    "progress_hooks": [prog.hook],
    "paths": {"temp": "testing/temp", "home": "testing/home"},
    "logger": MyLogger(),
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    error_code = ydl.download(video_urls)

# help(yt_dlp.postprocessor)
