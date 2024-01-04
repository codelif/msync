import os
import platform
import shutil
import threading
import time
from typing import Any

from . import PROG


def get_user_data_folder(make_folder: bool = True) -> str:
    """Returns OS-specific application user data storage folder. Makes the directory if not present.

    Returns:
        str: user data storage folder
    """
    match platform.system().lower():
        case "darwin":
            user_data = os.path.expanduser("~/Library/Application Support")
        case "linux":
            user_data = os.environ.get("XDG_DATA_HOME")
            if not user_data:
                user_data = os.path.expanduser("~/.local/share")
        case "windows":
            user_data = os.environ["APPDATA"]

    user_data = os.path.join(user_data, PROG)
    if make_folder:
        os.makedirs(user_data, exist_ok=True)
    return user_data


def get_user_config_folder(make_folder: bool = True) -> str:
    """Returns OS-specific application user data storage folder. Makes the directory if not present.

    Returns:
        str: user data storage folder
    """
    match platform.system().lower():
        case "darwin":
            user_config = os.path.expanduser("~/Library/Preferences")
        case "linux":
            user_config = os.environ.get("XDG_CONFIG_HOME")
            if not user_config:
                user_config = os.path.expanduser("~/.config")
        case "windows":
            user_config = os.environ["APPDATA"]

    user_config = os.path.join(user_config, PROG)
    if make_folder:
        os.makedirs(user_config, exist_ok=True)
    return user_config


class StyledThread(threading.Thread):
    """StyledThread class.

    Inherits python's threading.Thread class. Adds changes to return target value and styled waiting.
    """

    def __init__(
        self, group=None, target=None, name=None, args=(), kwargs={}, Verbose=None
    ):
        threading.Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        threading.Thread.join(self, *args)
        return self._return

    def styled_join(
        self, description: str, dot_interval: float = 0.25, dot_style: str = "."
    ) -> Any:
        """Waits for thread termination with waiting animation. Returns target return value

        Args:
            description (str): Text in waiting animation
            dot_interval (float, optional): Animation speed. Defaults to 0.5.
            dot_style (str, optional): Character to use in animation. Defaults to "."

        Returns:
            Any: Target's return value
        """
        dot_count = 0
        while self.is_alive():
            if dot_count > 3:
                dot_count = 0
            text = description + (dot_style * dot_count)
            remaining_term_columns = shutil.get_terminal_size().columns - len(text) - 1

            print(text, remaining_term_columns * " ", end="\r")

            dot_count += 1
            time.sleep(dot_interval)

        print(" " * shutil.get_terminal_size().columns, end="\r")

        return self.join()
