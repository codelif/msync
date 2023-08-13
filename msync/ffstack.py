import os
import platform
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile

import requests
from tqdm import tqdm

from .utils import get_user_data_folder

BUILDS = os.path.join(get_user_data_folder(), "ffmpeg_builds")


def is_ffmpeg_installed() -> str:
    """Returns 'system' if ffmpeg is in PATH otherwise empty string

    Returns:
        str: 'system' or ''
    """
    installed = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    if installed:
        return "system"
    return ""


def is_ffmpeg_local() -> str:
    """Returns 'local' if ffmpeg is installed in user-data folder.

    Returns:
        str: 'local' or ''
    """
    if not os.path.exists(BUILDS):
        return ""

    listdir = os.listdir(BUILDS)
    ffmpeg_in_builds = "ffmpeg" in listdir and "ffprobe" in listdir
    if not ffmpeg_in_builds:
        return ""

    subproc_options = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    try:  # Check for basic data corruption in binary
        subprocess.run([f"{BUILDS}/ffmpeg", "-hide_banner", "-L"], **subproc_options)
        subprocess.run([f"{BUILDS}/ffprobe", "-hide_banner", "-L"], **subproc_options)
    except OSError:
        return ""

    return "local"


def is_installed():
    return is_ffmpeg_local() or is_ffmpeg_installed()


def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(path, mode)


def download_file(url: str, fname: str, path: str, chunk_size=1024):
    resp = requests.get(url, stream=True)
    total = int(resp.headers.get("content-length", 0))
    with open(os.path.join(path, fname), "wb") as file, tqdm(
        desc=fname,
        total=total,
        unit="iB",
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in resp.iter_content(chunk_size=chunk_size):
            size = file.write(data)
            bar.update(size)


def unzip(zip: str, dst: str, progress_bar: bool = False):
    with ZipFile(file=zip) as zip_file:
        iterable = zip_file.namelist()
        caption = f"Extracting {os.path.basename(zip)}"
        if progress_bar:
            iterable = tqdm(
                desc=caption,
                iterable=iterable,
                total=len(iterable),
            )
        print(f"{caption}...")
        for file in iterable:
            zip_file.extract(member=file, path=dst)


def install_macos():
    MACOS_FFMPEG = "https://evermeet.cx/ffmpeg/getrelease/ffmpeg/zip"
    MACOS_FFPROBE = "https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip"
    FFMPEG_ZIP = "ffmpeg_latest_macos_x64.zip"
    FFPROBE_ZIP = "ffprobe_latest_macos_x64.zip"

    url_file_array = ((MACOS_FFMPEG, FFMPEG_ZIP), (MACOS_FFPROBE, FFPROBE_ZIP))

    with tempfile.TemporaryDirectory() as tmpdir:
        for url, file in url_file_array:
            download_file(url, file, tmpdir)
            unzip(os.path.join(tmpdir, file), BUILDS)
            make_executable(os.path.join(BUILDS, file.split("_")[0]))
            print()


def install_ffstack():
    host = platform.system().lower()
    match host:  # Fuck you backwards-compatibility, I like match-cases!
        case "darwin":
            install_macos()
        case "linux":
            print(
                "ERROR: We do not support automatic ffmpeg (,ffprobe) installation for linux.\nPlease install ffmpeg using your distribution's package manager. It is a much better solution than downloading multiple binaries for same program."
            )
            sys.exit(1)
        case "windows":
            print("BULLSHIT: WTF are you doing here with Windows!.")
            sys.exit(1)


def where():
    """Where are FFmpeg binaries?"""
    installed = is_installed()

    match installed:
        case "system":
            dirname = os.path.dirname(shutil.which("ffmpeg"))
        case "local":
            dirname = BUILDS
        case _:
            dirname = ""

    return dirname
