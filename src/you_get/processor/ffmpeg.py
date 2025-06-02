#!/usr/bin/env python

"""
ffmpeg.py

A module for handling video concatenation and conversion using FFmpeg.

Functions:
    get_usable_ffmpeg
    has_ffmpeg_installed
    generate_concat_list
    ffmpeg_concat_av
    ffmpeg_concat_mp4_to_mpg
    ffmpeg_concat_ts_to_mkv
    ffmpeg_concat_flv_to_mp4
    ffmpeg_concat_mp3_to_mp3
    ffmpeg_concat_mp4_to_mp4
    ffmpeg_download_stream

"""

import logging
import os
from typing import List, Generator, Tuple, Optional
import subprocess
import shlex
import time

from pathlib import Path

from ..util.strings import parameterize
from ..common import print_more_compatible as print_compat

try:
    from subprocess import DEVNULL
except ImportError:
    # The following code is for Python 3.2 or below.
    import os
    import atexit
    DEVNULL = os.open(os.devnull, os.O_RDWR)
    atexit.register(lambda fd: os.close(fd), DEVNULL)

__all__ = [
    'get_usable_ffmpeg', 'has_ffmpeg_installed', 'generate_concat_list',
    'ffmpeg_concat_av', 'ffmpeg_concat_mp4_to_mpg', 'ffmpeg_concat_ts_to_mkv',
    'ffmpeg_concat_flv_to_mp4', 'ffmpeg_concat_mp3_to_mp3', 'ffmpeg_concat_mp4_to_mp4',
    'ffmpeg_download_stream', 'ffmpeg_concat_audio_and_video', 'ffprobe_get_media_duration'
]

COPY_COMMAND = '-c'
INPUT_FLAG = '-i'
OVERWRITE_FLAG = '-y'
END_FLAG = '--'


def prepare_ffmpeg_params(file: str, output: str) -> List[str]:
    """
    Prepares the FFMPEG command parameters for a given file and output.

    Args:
        file (str): The input file path.
        output (str): The output file path.

    Returns:
        List[str]: The prepared FFMPEG command parameters.
    """
    return [FFMPEG] + LOGLEVEL + ['-y', '-i', file, '--', output]


def get_usable_ffmpeg(
    cmd: str
) -> Optional[Tuple[str, str, List[int]]]:
    """
    Attempts to run the given command using subprocess and checks if ffmpeg
    is usable. If successful, returns the command, 'ffprobe', and the
    version of ffmpeg. Otherwise, returns None.

    Args:
        cmd (str): The command to execute, typically the path to the ffmpeg
        executable.

    Returns:
        tuple[str, str, list[int]]: A tuple containing the command, 'ffprobe', and
        the version of ffmpeg.
    """
    try:
        p = subprocess.Popen(
            [cmd, '-version'],
            stdin=DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        out, err = p.communicate()
        if p.returncode != 0:
            logging.error(f'Error getting a usable ffmpeg version: {err.decode()}')
            return None
        vers = str(out, 'utf-8').split('\n')[0].split()
        is_ffmpeg = vers[0] == 'ffmpeg' and vers[2][0] > '0'
        is_avconv = version[0] == 'avconv'
        assert is_ffmpeg or is_avconv
        try:
            v = vers[2][1:] if vers[2][0] == 'n' else vers[2]
            version = [int(i) for i in v.split('.')]
        except Exception as e:
            logging.error(f'Error parsing ffmpeg version: {e}')
            version = [1, 0]
        return cmd, 'ffprobe', version
    except (subprocess.CalledProcessError, AssertionError, IndexError):
        return None

FFMPEG, FFPROBE, FFMPEG_VERSION = get_usable_ffmpeg('ffmpeg') or get_usable_ffmpeg('avconv') or (None, None, None)
if logging.getLogger().isEnabledFor(logging.DEBUG):
    LOGLEVEL = ['-loglevel', 'info']
    STDIN = None
else:
    LOGLEVEL = ['-loglevel', 'quiet']
    STDIN = DEVNULL


def has_ffmpeg_installed() -> bool:
    """
    Check if the ffmpeg command is available.

    Returns:
        bool: True if ffmpeg is available, else False.
    """
    if not FFMPEG:
        logging.warning("FFmpeg not found.")
    return bool(FFMPEG)


def check_format_compatibility(files: List[str], output_format: str) -> bool:
    """Check if the input files are compatible with the desired output format."""
    output_format = output_format.lower()
    return all(file.endswith(output_format) for file in files)


# Given a list of segments and the output path, generates the concat
# list and returns the path to the concat list.
def generate_concat_list(
    files: List[str], output: str
) -> str:
    """
    Generates a concatenation list for video files.

    Args:
        files (List[str]): A list of files to be concatenated.
        output (str): The output file path.

    Returns:
        str: The path to the generated concatenation list.
    """
    concat_list_path = os.path.join(os.path.dirname(output), os.path.basename(output) + '.txt')
    concat_list_dir = os.path.abspath()
    with open(concat_list_path, 'w', encoding='utf-8', buffering=8192) as concat_list:
        for file in files:
            if Path(file).is_file():
                relpath = os.path.relpath(file, start=concat_list_dir)
                concat_list.write(f'file {shlex.quote(parameterize(relpath))}\n')
    return concat_list_path


def ffmpeg_concat_av(files: List[str], output: str, ext: str) -> int:
    """
    Concatenates video files using ffmpeg.

    Args:
        files (List[str]): A list of video files to be concatenated.
        output (str): The output file path.
        ext (str): The extension of the output file.

    Returns:
        int: The exit code of the subprocess call. 0 indicates success.
    """
    print('Merging video parts... ', end="", flush=True)
    params = [FFMPEG] + LOGLEVEL
    input_files = [file for file in files if os.path.isfile(file)]
    if len(input_files) > 0:
        params.extend(['-i', '|'.join(input_files)])
    params.extend(['-c', 'copy'])
    params.extend(['--', output])
    if subprocess.call(params, stdin=STDIN):
        print('Merging without re-encode failed.\nTry again re-encoding audio... ', end="", flush=True)
        if os.path.exists(output):
            os.remove(output)
        params = [FFMPEG] + LOGLEVEL
        valid_files = list(filter(os.path.isfile, files))
        for file in valid_files:
            params.extend(['-i', file])
        params.extend(['-c:v', 'copy'])
        if ext == 'mp4':
            params.extend(['-c:a', 'aac'])
            params.extend(['-strict', 'experimental'])
        elif ext == 'webm':
            params.extend(['-c:a', 'opus'])
        params.extend(['--', output])
        return subprocess.run(params, stdin=STDIN, check=True)
    else:
        return 0


def lazy_file_reader(files: List[str]) -> Generator[bytes, None, None]:
    """Lazily reads a list of files with a .mpg extension.

    Args:
        files (List[str]): A list of file paths (without extensions).

    Yields:
        bytes: The content of each file.
    """
    for file in files:
        with open(file + '.mpg', 'rb') as f:
            yield f.read()


def ffmpeg_convert_ts_to_mkv(files: List[str], output: str ='output.mkv') -> None:
    """Converts a list of .ts files to .mkv files.

    Args:
        files (List[str]): A list of .ts file paths to be converted.
        output (str): The output file path.
    """
    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG, '-y', '-i', file, '--', output] + LOGLEVEL
            subprocess.run(params, stdin=STDIN, check=True)


def ffmpeg_concat_mp4_to_mpg(files: List[str], output: str = 'output.mpg') -> bool:
    """
    Concatenates video files into an MPG file using ffmpeg.

    Args:
        files (List[str]): A list of video files to be concatenated.
        output (str): The output file path.

    Returns:
        bool: True if the concatenation was successful, else False.
    """
    # Use concat demuxer on FFmpeg >= 1.1
    if FFMPEG == 'ffmpeg' and (
        FFMPEG_VERSION[0] >= 2 or (FFMPEG_VERSION[0] == 1 and FFMPEG_VERSION[1] >= 1)
    ):
        concat_list = generate_concat_list(files, output)
        params = [FFMPEG] + LOGLEVEL + ['-y', '-f', 'concat', '-safe', '0',
                                        '-i', concat_list, '-c', 'copy']
        params.extend(['--', output])
        result = subprocess.run(params, stdin=STDIN, check=True)
        if result.returncode == 0:
            os.remove(f"{output}.txt")
            return True
        else:
            raise RuntimeError("ffmpeg concat failed")

    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
            params.extend([file, file + '.mpg'])
            subprocess.run(params, stdin=STDIN)

    with open(output + '.mpg', 'wb') as o:
        o.writelines(lazy_file_reader(files))

    params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
    params.append(output + '.mpg')
    params += ['-vcodec', 'copy', '-acodec', 'copy']
    params.extend(['--', output])

    if subprocess.call(params, stdin=STDIN) == 0:
        for file in files:
            os.remove(file + '.mpg')
        os.remove(output + '.mpg')
        return True
    else:
        raise


def ffmpeg_concat_ts_to_mkv(files: List[str], output: str = 'output.mkv') -> bool:
    """
    Concatenates video files into an MKV file using ffmpeg.

    Args:
        files (List[str]): A list of video files to be concatenated.
        output (str): The output file path.

    Returns:
        bool: True if the concatenation was successful, else False.
    """
    print('Merging video parts... ', end="", flush=True)
    params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
    # Use the concat protocol for compatible files; available 
    params.append('concat:')
    valid_files = filter(os.path.isfile, files)
    for file in valid_files:
        params[-1] += file + '|'
    params += ['-f', 'matroska', '-c', 'copy']
    params.extend(['--', output])

    try:
        if subprocess.call(params, stdin=STDIN) == 0:
            return True
        else:
            return False
    except (OSError, subprocess.CalledProcessError):
        return False


def ffmpeg_concat_flv_to_mp4(files: List[str], output='output.mp4') -> bool:
    """
    Concatenates video files into an MP4 file using ffmpeg.

    Args:
        files (List[str]): A list of video files to be concatenated.
        output (str): The output file path.

    Returns:
        bool: True if the concatenation was successful, else False.
    """
    print('Merging video parts... ', end="", flush=True)
    # Use concat demuxer on FFmpeg >= 1.1
    if FFMPEG == 'ffmpeg' and (FFMPEG_VERSION[0] >= 2 or (FFMPEG_VERSION[0] == 1 and FFMPEG_VERSION[1] >= 1)):
        concat_list = generate_concat_list(files, output)
        params = [FFMPEG] + LOGLEVEL + ['-y', '-f', 'concat', '-safe', '0',
                                        '-i', concat_list, '-c', 'copy',
                                        '-bsf:a', 'aac_adtstoasc']
        params.extend(['--', output])
        subprocess.check_call(params, stdin=STDIN)
        os.remove(output + '.txt')
        return True

    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG] + LOGLEVEL + ['-i', '-y']
            params.append(file)
            params += ['-map', '0', '-c', 'copy', '-f', 'mpegts', '-bsf:v', 'h264_mp4toannexb']
            params.append(file + '.ts')

            subprocess.call(params, stdin=STDIN, check=True)

    params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
    params.append('concat:')
    for file in files:
        f = file + '.ts'
        if os.path.isfile(f):
            params[-1] += f + '|'
    if FFMPEG == 'avconv':
        params += ['-c', 'copy']
    else:
        params += ['-c', 'copy', '-bsf:a', 'aac_adtstoasc']
    params.extend(['--', output])

    if subprocess.call(params, stdin=STDIN) == 0:
        for file in files:
            os.remove(file + '.ts')
        return True
    else:
        raise

def ffmpeg_concat_mp3_to_mp3(files: List[str], output: str = 'output.mp3'):
    """
    Concatenates multiple MP3 files into a single MP3 file.

    Args:
        files (List[str]): A list of MP3 file paths to be concatenated.
        output (str): The output file path.

    Returns:
        bool: True if the concatenation was successful, else False.
    """
    print('Merging video parts... ', end="", flush=True)

    files = f"concat:{'|'.join(files)}"

    params = [FFMPEG] + LOGLEVEL + ['-y']
    params += ['-i', files, '-acodec', 'copy']
    params.extend(['--', output])
    try:
        subprocess.run(params)
    except Exception as e:
        logging.error(f"Error while concatenating MP3 files: {e}")
        return False
    return True

def ffmpeg_concat_mp4_to_mp4(files: List[str], output: str = 'output.mp4'):
    """
    Concatenates multiple MP4 files into a single MP4 file.

    Args:
        files (List[str]): A list of MP4 file paths to be concatenated.
        output (str): The output file path.

    Returns:
        bool: True if the concatenation was successful, else False.
    """
    print('Merging video parts... ', end="", flush=True)
    # Use concat demuxer on FFmpeg >= 1.1
    if FFMPEG == 'ffmpeg' and (FFMPEG_VERSION[0] >= 2 or (FFMPEG_VERSION[0] == 1 and FFMPEG_VERSION[1] >= 1)):
        concat_list = generate_concat_list(files, output)
        params = [FFMPEG] + LOGLEVEL + ['-y', '-f', 'concat', '-safe', '0',
                                        '-i', concat_list, '-c', 'copy',
                                        '-bsf:a', 'aac_adtstoasc']
        params.extend(['--', output])
        subprocess.check_call(params, stdin=STDIN)
        os.remove(output + '.txt')
        return True

    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
            params.append(file)
            params += ['-c', 'copy', '-f', 'mpegts', '-bsf:v', 'h264_mp4toannexb']
            params.append(file + '.ts')
            try:
                subprocess.run(params, stdin=STDIN, check=True)
                time.sleep(0.01)
            except FileNotFoundError:
                logging.error(
                    "FFmpeg binary not found. Ensure it's installed and accessible."
                    " If it's installed, check your PATH environment variable."
                )

    params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
    params.append('concat:')
    for file in files:
        f = file + '.ts'
        if os.path.isfile(f):
            params[-1] += f + '|'
    if FFMPEG == 'avconv':
        params += ['-c', 'copy']
    else:
        params += ['-c', 'copy', '-bsf:a', 'aac_adtstoasc']
    params.extend(['--', output])

    subprocess.check_call(params, stdin=STDIN)
    for file in files:
        os.remove(file + '.ts')
    return True


def ffmpeg_download_stream(files, title, ext, params=None, output_dir='.', stream: bool = True):
    """str, str->True
    WARNING: NOT THE SAME PARMS AS OTHER FUNCTIONS!!!!!!
    You can basically download anything with this function
    but this function should not be used unless you know what you're doing
    """
    if params is None:
        params = {}
    output = title + '.' + ext

    if not (output_dir == '.'):
        output = output_dir + '/' + output

    print('Downloading streaming content with FFmpeg, press q to stop recording...')
    ffmpeg_params = [FFMPEG, '-y', '-re'] if stream else [FFMPEG, '-y']
    ffmpeg_params.append('-i')
    ffmpeg_params.append(files)  #not the same here!!!!

    if FFMPEG == 'avconv':  #who cares?
        ffmpeg_params += ['-c', 'copy']
    else:
        ffmpeg_params += ['-c', 'copy', '-bsf:a', 'aac_adtstoasc']

    if params is not None:
        if len(params) > 0:
            for k, v in params:
                ffmpeg_params.append(k)
                ffmpeg_params.append(v)

    ffmpeg_params.extend(['--', output])

    print(shlex.join(ffmpeg_params))

    try:
        a = subprocess.Popen(ffmpeg_params, stdin=subprocess.PIPE)
        a.communicate()
    except KeyboardInterrupt:
        logging.info(
            "Download interrupted by user. Attempting to stop"
            " s..."
        )
        try:
            a.stdin.write('q'.encode('utf-8'))
        except BrokenPipeError:
            logging.error("Error stopping download stream: BrokenPipeError")

    return True


def ffmpeg_concat_audio_and_video(files: List[str], output: str, ext: str) -> int:
    """
    Concatenates audio and video files into a single file.

    Args:
        files (List[str]): A list of files to be concatenated.
        output (str): The output file path.
        ext (str): The extension of the output file.

    Returns:
        int: The exit code of the subprocess call.
    """
    print('Merging video and audio parts... ', end="", flush=True)
    if has_ffmpeg_installed():
        params = [FFMPEG] + LOGLEVEL
        params.extend(['-f', 'concat'])
        params.extend(['-safe', '0'])  # https://stackoverflow.com/questions/38996925/ffmpeg-concat-unsafe-file-name
        valid_files = [file for file in files if os.path.isfile(file)]
        for file in valid_files:
            params.extend(['-i', file])
        params.extend(['-c:v', 'copy'])
        params.extend(['-c:a', 'aac'])
        params.extend(['-strict', 'experimental'])
        params.extend(['--', output + "." + ext])
        return subprocess.call(params, stdin=STDIN)
    else:
        raise RuntimeError("ffmpeg is not installed")


def ffprobe_get_media_duration(file: str) -> str:
    """
    Gets the duration of a media file using ffprobe.

    Args:
        file (str): The path to the media file.

    Returns:
        str: The duration of the media file in seconds.
    """
    print(f'Getting {file} duration')
    params = [FFPROBE]
    params.extend(['-i', file])
    params.extend(['-show_entries', 'format=duration'])
    params.extend(['-v', 'quiet'])
    params.extend(['-of', 'csv=p=0'])
    return subprocess.check_output(
        params, stdin=STDIN, stderr=subprocess.STDOUT
    ).decode().strip()
