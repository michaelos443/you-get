#!/usr/bin/env python

"""
rtmpdump.py

A module for handling RTMP streams using rtmpdump.
"""

import logging
import subprocess
from functools import lru_cache
from pathlib import Path
from shlex import quote
from typing import Optional
from urllib.parse import urlparse


# def construct_command()


def validate_url(url: str) -> None:
    """
    Validates the URL scheme to ensure it starts with 'rtmp'.

    Args:
        url (str): The URL to validate.

    Raises:
        ValueError: If the URL scheme is not 'rtmp'.
    """
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.scheme.startswith("rtmp"):
        raise ValueError(f"Invalid URL scheme: {url}")


@lru_cache(maxsize=1)
def get_usable_rtmpdump(cmd: str) -> Optional[str]:
    """
    Attempts to run the given command using subprocess and checks if rtmpdump is usable.
    If successful, returns the command. Otherwise, returns None.

    Args:
        cmd (str): The command to execute, typically the path to the rtmpdump executable.

    Returns:
        Optional[str]: The command if successful, or None if an error occurs.
    """
    try:
        p = subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        p.wait()
        return cmd
    except FileNotFoundError:
        logging.error(f"rtmpdump is not installed or not usable on this system: {cmd}")
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"rtmpdump command failed: {e}")
        return None

if __name__ == "__main__":
    if not (RTMPDUMP := get_usable_rtmpdump('rtmpdump')):
        raise RuntimeError("rtmpdump is not installed or not usable on this system.")


def run_command(command: list) -> subprocess.CompletedProcess:
    """
    Runs a command using subprocess and returns the CompletedProcess instance.
    Args:
        command (list): The command to execute as a list of arguments.
    Returns:
        subprocess.CompletedProcess: The result of the subprocess execution.
    """
    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
        shell=True,
    )


def create_filepath(
    output_dir: str, title: str, ext: str
) -> str:
    """
    Constructs a file path by joining the output directory, title and extension.

    Args:
        output_dir(str): The directory where the file would be saved.
        title(str): The title of the file.
        ext(str): The extension of the file.

    Returns:
        str: The constructed file path.
    """
    return str(Path(output_dir) / f"{title}.{ext}")


def has_rtmpdump_installed() -> bool:
    """
    Check if the rtmpdump command is available.

    Returns:
        bool: True if rtmpdump is available, False otherwise.
    """
    return get_usable_rtmpdump('rtmpdump') is not None


def download_rtmpdump_stream(
    url: str, title: str, ext: str, params: Optional[dict] = None, output_dir: str = '.'
) -> None:
    """
    Downloads a stream using rtmpdump, saving it to the specified file path.

    Args:
        url (str): The RTMP stream URL.
        title (str): The title of the file.
        ext (str): The extension of the file.
        params (dict, optional): Additional parameters for the rtmpdump command. Defaults to an empty dictionary.
        output_dir (str, optional): The directory where the file would be saved. Defaults to the current directory.

    Raises:
        OSError: If there is an error while calling rtmpdump.
        subprocess.CalledProcessError: If there is an error while calling rtmpdump.

    """
    # Default empty dictionary for params if not provided.
    if params is None:
        params = {}
    filepath = create_filepath(
        output_dir,
        title.strip(),
        ext.lower()
    )

    cmdline = [RTMPDUMP, '-r']
    cmdline.extend([url, '-o', filepath])

    for key, value in params.items():
        if value is not None:
            cmdline.append(quote(value))

    # cmdline.append('-y')
    # cmdline.append(playpath)
    print(f"Call rtmpdump:\n{' '.join(cmdline)}\n")
    try:
        subprocess.call(cmdline, check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        logging.error(
            f"Error while calling rtmpdump: {e} "
            f"Command output: {e.output if hasattr(e, 'output') else 'N/A'}"
        )
        raise
    return


def play_rtmpdump_stream(
        player: str, url: str, params: Optional[dict] = None):
    """
    Constructs and executes an RTMP stream command using rtmpdump and a media player.
    This function executes the rtmpdump command to fetch the RTMP stream and pipe it to
    the specified player.

    Args:
        player (str): The media player command to pipe the stream to.
        url (str): The RTMP stream URL.
        params (dict, optional): Additional parameters for the rtmpdump command.
    """
    params = params 
    if not url.startswith('rtmp://'):
        url = 'rtmp://' + url

    # Construct left side of pipe, 
    cmdline = [RTMPDUMP, '-r']
    cmdline.append(url)

    # append other params if exist
    for key in params.keys():
        cmdline.append(quote(key))
        if params[key] is not None:
            cmdline.append(quote(params[key]))

    cmdline.append('-o')
    cmdline.append('-')

    # Pipe start
    cmdline.append('|')
    cmdline.append(player)
    cmdline.append('-')

    # Logging
    logging.info(f"Call rtmpdump: {' '.join(cmdline)}")

    # Call RTMPDump!
    subprocess.run(cmdline)
