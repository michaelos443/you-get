#!/usr/bin/env python

import logging
import os
import subprocess
import sys
from ..util.strings import parameterize
from ..common import print_more_compatible as print

try:
    from subprocess import DEVNULL
except ImportError:
    # Python 3.2 or below
    import os
    import atexit
    DEVNULL = os.open(os.devnull, os.O_RDWR)
    atexit.register(lambda fd: os.close(fd), DEVNULL)

def get_usable_ffmpeg(cmd):
    """Check if ffmpeg/avconv is available and return its information.

    This function checks if the given command (ffmpeg or avconv) is available in the system
    and returns the command, its probe command, and version information.

    Args:
        cmd (str): The command to check, either 'ffmpeg' or 'avconv'

    Returns:
        tuple or None: A tuple containing (command, probe_command, version) if the command
                      is available, or None if it's not available or an error occurs.
                      The version is a list of integers representing the version numbers.
    """
    logger = logging.getLogger('ffmpeg')
    try:
        # Run the command with -version flag to get version information
        p = subprocess.Popen([cmd, '-version'], stdin=DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()

        # Check if the process returned successfully
        if p.returncode != 0:
            logger.debug(f"{cmd} returned non-zero exit code: {p.returncode}")
            return None

        # Parse the output to get version information
        vers = str(out, 'utf-8').split('\n')[0].split()

        # Verify it's either ffmpeg or avconv
        if not ((vers[0] == 'ffmpeg' and vers[2][0] > '0') or (vers[0] == 'avconv')):
            logger.debug(f"Unexpected version format from {cmd}: {vers}")
            return None

        # Parse version number
        try:
            # Handle ffmpeg version format which might start with 'n'
            v = vers[2][1:] if vers[2][0] == 'n' else vers[2]
            # Convert version string to list of integers
            version = [int(i) for i in v.split('.')]
        except (IndexError, ValueError) as e:
            logger.debug(f"Error parsing version for {cmd}: {e}")
            # Default to version 1.0 if parsing fails
            version = [1, 0]

        # Determine the probe command based on the command
        probe_cmd = 'ffprobe' if cmd == 'ffmpeg' else 'avprobe'
        return cmd, probe_cmd, version
    except Exception as e:
        logger.debug(f"Error checking {cmd}: {e}")
        return None

FFMPEG, FFPROBE, FFMPEG_VERSION = get_usable_ffmpeg('ffmpeg') or get_usable_ffmpeg('avconv') or (None, None, None)
if logging.getLogger().isEnabledFor(logging.DEBUG):
    LOGLEVEL = ['-loglevel', 'info']
    STDIN = None
else:
    LOGLEVEL = ['-loglevel', 'quiet']
    STDIN = DEVNULL

def has_ffmpeg_installed():
    return FFMPEG is not None

def generate_concat_list(files, output):
    """Generate a concat list file for FFmpeg.

    This function creates a text file listing all input files in the format
    required by FFmpeg's concat demuxer. It handles file paths with special
    characters by using the parameterize function.

    Args:
        files (list): List of file paths to be concatenated
        output (str): Output file path (without the .txt extension)

    Returns:
        str: Path to the generated concat list file

    Raises:
        IOError: If there's an error writing the concat list file
    """
    logger = logging.getLogger('ffmpeg')
    concat_list_path = output + '.txt'
    concat_list_dir = os.path.dirname(concat_list_path)

    # Create directory if it doesn't exist
    if concat_list_dir and not os.path.exists(concat_list_dir):
        try:
            os.makedirs(concat_list_dir)
        except OSError as e:
            logger.error(f"Failed to create directory {concat_list_dir}: {e}")
            raise

    valid_files = [f for f in files if os.path.isfile(f)]
    if not valid_files:
        logger.warning("No valid files found for concatenation")

    try:
        with open(concat_list_path, 'w', encoding='utf-8') as concat_list:
            for file in files:
                if os.path.isfile(file):
                    # Get relative path to avoid issues with absolute paths
                    relpath = os.path.relpath(file, start=concat_list_dir)
                    # Escape special characters in the path
                    concat_list.write(f"file {parameterize(relpath)}\n")
        return concat_list_path
    except IOError as e:
        logger.error(f"Failed to write concat list file {concat_list_path}: {e}")
        raise

def ffmpeg_concat_av(files, output, ext):
    """Concatenate audio/video files using FFmpeg.

    This function attempts to merge multiple audio/video files into a single file.
    It first tries to copy both audio and video streams without re-encoding.
    If that fails, it tries again with audio re-encoding based on the output format.

    Args:
        files (list): List of file paths to be concatenated
        output (str): Output file path
        ext (str): Output file extension/format (e.g., 'mp4', 'webm')

    Returns:
        int: 0 on success, non-zero on failure
    """
    logger = logging.getLogger('ffmpeg')
    print('Merging video parts... ', end="", flush=True)

    # Filter out non-existent files
    valid_files = [f for f in files if os.path.isfile(f)]
    if not valid_files:
        logger.error("No valid files found for concatenation")
        return 1

    # First attempt: try to copy both audio and video streams without re-encoding
    params = [FFMPEG] + LOGLEVEL
    for file in valid_files:
        params.extend(['-i', file])
    params.extend(['-c', 'copy', '--', output])

    try:
        result = subprocess.call(params, stdin=STDIN)
        if result == 0:
            return 0  # Success
    except Exception as e:
        logger.error(f"Error during first concatenation attempt: {e}")
        result = 1  # Force retry with re-encoding

    # If first attempt failed, try again with audio re-encoding
    print('Merging without re-encode failed.\nTry again re-encoding audio... ', end="", flush=True)

    # Remove output file if it exists (might be partially created)
    try:
        if os.path.exists(output):
            os.remove(output)
    except OSError as e:
        logger.warning(f"Failed to remove partial output file: {e}")

    # Second attempt: copy video stream but re-encode audio based on format
    params = [FFMPEG] + LOGLEVEL
    for file in valid_files:
        params.extend(['-i', file])

    # Always copy video stream to avoid quality loss
    params.extend(['-c:v', 'copy'])

    # Select audio codec based on output format
    if ext == 'mp4':
        params.extend(['-c:a', 'aac', '-strict', 'experimental'])
    elif ext == 'webm':
        params.extend(['-c:a', 'opus'])
    else:
        # For other formats, try to copy audio or use a default codec
        params.extend(['-c:a', 'copy'])

    params.extend(['--', output])

    try:
        return subprocess.call(params, stdin=STDIN)
    except Exception as e:
        logger.error(f"Error during second concatenation attempt: {e}")
        return 1

def ffmpeg_convert_ts_to_mkv(files, output='output.mkv'):
    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG] + LOGLEVEL
            params.extend(['-y', '-i', file])
            params.extend(['--', output])
            subprocess.call(params, stdin=STDIN)

    return

def ffmpeg_concat_mp4_to_mpg(files, output='output.mpg'):
    # Use concat demuxer on FFmpeg >= 1.1
    if FFMPEG == 'ffmpeg' and (FFMPEG_VERSION[0] >= 2 or (FFMPEG_VERSION[0] == 1 and FFMPEG_VERSION[1] >= 1)):
        concat_list = generate_concat_list(files, output)
        params = [FFMPEG] + LOGLEVEL + ['-y', '-f', 'concat', '-safe', '0',
                                        '-i', concat_list, '-c', 'copy']
        params.extend(['--', output])
        if subprocess.call(params, stdin=STDIN) == 0:
            os.remove(output + '.txt')
            return True
        else:
            raise

    for file in files:
        if os.path.isfile(file):
            params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
            params.extend([file, file + '.mpg'])
            subprocess.call(params, stdin=STDIN)

    inputs = [open(file + '.mpg', 'rb') for file in files]
    with open(output + '.mpg', 'wb') as o:
        for input in inputs:
            o.write(input.read())

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

def ffmpeg_concat_ts_to_mkv(files, output='output.mkv'):
    print('Merging video parts... ', end="", flush=True)
    params = [FFMPEG] + LOGLEVEL + ['-y', '-i']
    params.append('concat:')
    for file in files:
        if os.path.isfile(file):
            params[-1] += file + '|'
    params += ['-f', 'matroska', '-c', 'copy']
    params.extend(['--', output])

    try:
        if subprocess.call(params, stdin=STDIN) == 0:
            return True
        else:
            return False
    except:
        return False

def ffmpeg_concat_flv_to_mp4(files, output='output.mp4'):
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
            params += ['-map', '0', '-c', 'copy', '-f', 'mpegts', '-bsf:v', 'h264_mp4toannexb']
            params.append(file + '.ts')

            subprocess.call(params, stdin=STDIN)

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

def ffmpeg_concat_mp3_to_mp3(files, output='output.mp3'):
    print('Merging video parts... ', end="", flush=True)

    files = 'concat:' + '|'.join(files)

    params = [FFMPEG] + LOGLEVEL + ['-y']
    params += ['-i', files, '-acodec', 'copy']
    params.extend(['--', output])

    subprocess.call(params)

    return True

def ffmpeg_concat_mp4_to_mp4(files, output='output.mp4'):
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

            subprocess.call(params, stdin=STDIN)

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

def ffmpeg_download_stream(files, title, ext, params={}, output_dir='.', stream=True):
    """str, str->True
    WARNING: NOT THE SAME PARMS AS OTHER FUNCTIONS!!!!!!
    You can basically download anything with this function
    but better leave it alone with
    """
    output = title + '.' + ext

    if not (output_dir == '.'):
        output = output_dir + '/' + output

    print('Downloading streaming content with FFmpeg, press q to stop recording...')
    if stream:
        ffmpeg_params = [FFMPEG] + ['-y', '-re', '-i']
    else:
        ffmpeg_params = [FFMPEG] + ['-y', '-i']
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

    print(' '.join(ffmpeg_params))

    try:
        a = subprocess.Popen(ffmpeg_params, stdin= subprocess.PIPE)
        a.communicate()
    except KeyboardInterrupt:
        try:
            a.stdin.write('q'.encode('utf-8'))
        except:
            pass

    return True


def ffmpeg_concat_audio_and_video(files, output, ext):
    print('Merging video and audio parts... ', end="", flush=True)
    if has_ffmpeg_installed:
        params = [FFMPEG] + LOGLEVEL
        params.extend(['-f', 'concat'])
        params.extend(['-safe', '0'])  # https://stackoverflow.com/questions/38996925/ffmpeg-concat-unsafe-file-name
        for file in files:
            if os.path.isfile(file):
                params.extend(['-i', file])
        params.extend(['-c:v', 'copy'])
        params.extend(['-c:a', 'aac'])
        params.extend(['-strict', 'experimental'])
        params.extend(['--', output + "." + ext])
        return subprocess.call(params, stdin=STDIN)
    else:
        raise EnvironmentError('No ffmpeg found')


def ffprobe_get_media_duration(file):
    print('Getting {} duration'.format(file))
    params = [FFPROBE]
    params.extend(['-i', file])
    params.extend(['-show_entries', 'format=duration'])
    params.extend(['-v', 'quiet'])
    params.extend(['-of', 'csv=p=0'])
    return subprocess.check_output(params, stdin=STDIN, stderr=subprocess.STDOUT).decode().strip()
