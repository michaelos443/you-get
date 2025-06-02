#!/usr/bin/env python

__all__ = ['letv_download', 'letvcloud_download', 'letvcloud_download_by_vu']

import base64
import hashlib
import re
import random
import requests
from urllib import parse
from typing import Union, Dict, Any, Tuple, List

from ..common import *

LE_TV_CLOUD_API_BASE_URL = 'http://api.letvcloud.com/'


# @DEPRECATED
def get_timestamp():
    tn = random.random()
    url = 'http://api.letv.com/time?tn={}'.format(tn)
    try:
        result = get_content(url)
    except Exception as e:
        print(f"Error retrieving content from {url}: {e}")
        return None
    return json.loads(result)['stime']


# @DEPRECATED
def get_key(t: int) -> int:
    for s in range(0, 8):
        e = 1 & t
        t >>= 1
        e <<= 31
        t += e
    return t ^ 185025305


def calcTimeKey(t: int) -> int:
    """
    Calculates a time-based key using bitwise operations.

    Args:
        t (int): A timestamp used for the calculation.

    Returns:
        int: The calculated time-based key.
    """
    ror = lambda val, r_bits,: ((val & (2 ** 32 - 1)) >> r_bits % 32) | (val << (32 - (r_bits % 32)) & (2 ** 32 - 1))
    magic = 185025305
    return ror(t, magic % 17) ^ magic
    # return ror(ror(t,773625421%13)^773625421,773625421%17)


def decode(data: bytes) -> Union[str, bytes]:
    """Decodes the given data based on its version.

    Args:
        data (bytes): The input data to decode, expected to be in bytes format.

    Returns:
        Union[str, bytes]: The decoded string if the version is 'vc_01', 
                           otherwise returns the original data as a string.
    """
    version = data[0:5]
    if version.lower() == b'vc_01':
        # get real m3u8
        loc2 = data[5:]
        length = len(loc2)
        loc4 = [0] * (2 * length)
        for i in range(length):
            loc4[2 * i] = loc2[i] >> 4
            loc4[2 * i + 1] = loc2[i] & 15;
        loc6 = loc4[len(loc4) - 11:] + loc4[:len(loc4) - 11]
        loc7 = [0] * length
        for i in range(length):
            loc7[i] = (loc6[2 * i] << 4) + loc6[2 * i + 1]
        return ''.join([chr(i) for i in loc7])
    else:
        # directly return
        return str(data)


def video_info(vid: str, **kwargs: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Retrieves video information and decodes the video URL(s) for a given video ID.
    """
    url = 'http://player-pc.le.com/mms/out/video/playJson?id={}&platid=1&splatid=105&format=1&tkey={}&domain=www.le.com&region=cn&source=1000&accesyx=1'.format(vid, calcTimeKey(int(time.time())))
    r = get_content(url, decoded=False)
    info = json.loads(str(r, "utf-8"))
    info = info['msgs']

    stream_id = None
    support_stream_id = info["playurl"]["dispatch"].keys()
    if "stream_id" in kwargs and kwargs["stream_id"].lower() in support_stream_id:
        stream_id = kwargs["stream_id"]
    else:
        preferred_streams = ["1080p","720p"]
        stream_id = next((s for s in preferred_streams if s in support_stream_id),
                         sorted(support_stream_id, key=lambda i: int(i[1:]))[-1])
        if "1080p" in support_stream_id:
            stream_id = '1080p'
        elif "720p" in support_stream_id:
            stream_id = '720p'
        else:
            stream_id = sorted(support_stream_id, key=lambda i: int(i[1:]))[-1]

    url = info["playurl"]["domain"][0] + info["playurl"]["dispatch"][stream_id][0]
    uuid = hashlib.sha1(url.encode('utf8')).hexdigest() + '_0'
    ext = info["playurl"]["dispatch"][stream_id][1].split('.')[-1]
    url = url.replace('tss=0', 'tss=ios')
    
    url_parts = [
        "&m3v=1", "&termid=1", "&format=1", "&hwtype=un", "&ostype=MacOS10.12.4",
        "&p1=1", "&p2=10", "&p3=-", "&expect=3", f"&tn={random.random()}", 
        f"&vid={vid}", f"&uuid={uuid}", "&sign=letv"
    ]
    url += ''.join(url_parts)
    r2 = get_content(url, decoded=False)
    info2 = json.loads(str(r2, "utf-8"))

    # hold on ! more things to do
    # to decode m3u8 (encoded)
    suffix = '&r=' + str(int(time.time() * 1000)) + '&appid=500'
    m3u8 = get_content(info2["location"] + suffix, decoded=False)
    m3u8_list = decode(m3u8)
    urls = re.findall(r'(http.*?)#', m3u8_list, re.MULTILINE)
    return ext, urls


def letv_download_by_vid(
        vid: str,
        title: str,
        output_dir: str = '.',
        merge: bool = True,
        info_only: bool = False,
        **kwargs: Dict[str, Any]
    ) -> None:
    ext, urls = video_info(vid, **kwargs)
    size = 0
    for i in urls:
        _, _, tmp = url_info(i)
        size += tmp

    print_info(site_info, title, ext, size)
    if not info_only:
        download_urls(urls, title, ext, size, output_dir=output_dir, merge=merge)


def letvcloud_download_by_vu(
        vu,
        uu,
        title=None,
        output_dir='.',
        merge=True,
        info_only=False
    ) -> None:
    """Downloads content from Letv Cloud based on the provided VU and UU.

    Args:
        vu (str): The VU parameter for the download.
        uu (str): The UU parameter for the download.
        title (str): The title of the video.
        output_dir (str): The directory to save downloaded files. Default is the current directory.
        merge (bool): Whether to merge files if applicable. Default is True.
        info_only (bool): If True, only show info without downloading. Default is False.
    """
    # ran = float('0.' + str(random.randint(0, 9999999999999999))) # For ver 2.1
    # str2Hash = 'cfflashformatjsonran{ran}uu{uu}ver2.2vu{vu}bie^#@(%27eib58'.format(vu = vu, uu = uu, ran = ran)  #Magic!/ In ver 2.1
    argumet_dict = {'cf': 'flash', 'format': 'json', 'ran': str(int(time.time())), 'uu': str(uu), 'ver': '2.2', 'vu': str(vu), }
    sign_key = '2f9d6924b33a165a6d8b5d3d42f4f987'  # ALL YOUR BASE ARE BELONG TO US
    str2Hash = ''.join([i + argumet_dict[i] for i in sorted(argumet_dict)]) + sign_key
    sign = hashlib.md5(str2Hash.encode('utf-8')).hexdigest()
    request_url = LE_TV_CLOUD_API_BASE_URL + 'gpc.php?' + '&'.join([i + '=' + argumet_dict[i] for i in argumet_dict]) + '&sign={sign}'.format(sign=sign)
    response = requests.get(request_url)
    data = response.content
    info = json.loads(data.decode('utf-8'))
    type_available = []
    for video_type in info['data']['video_info']['media']:
        type_available.append({'video_url': info['data']['video_info']['media'][video_type]['play_url']['main_url'], 'video_quality': int(info['data']['video_info']['media'][video_type]['play_url']['vtype'])})
    urls = [base64.b64decode(sorted(type_available, key=lambda x: x['video_quality'])[-1]['video_url']).decode("utf-8")]
    size = urls_size(urls)
    ext = 'mp4'
    print_info(site_info, title, ext, size)
    if not info_only:
        download_urls(urls, title, ext, size, output_dir=output_dir, merge=merge)


def letvcloud_download(
    url: str,
    output_dir: str = '.',
    merge: bool = True,
    info_only: bool = False
) -> None:
    """Downloads content from Letv Cloud based on the provided URL.

    Args:
        url (str): The URL containing the query parameters for the download.
        output_dir (str): The directory to save downloaded files. Default is the current directory.
        merge (bool): Whether to merge files if applicable. Default is True.
        info_only (bool): If True, only show info without downloading. Default is False.

    Raises:
        ValueError: If the required parameters are not found in the URL.
    """
    qs = parse.urlparse(url).query
    vu = match1(qs, r'vu=([\w]+)')
    uu = match1(qs, r'uu=([\w]+)')
    if not vu or not uu:
        raise ValueError("Required parameters not found in the URL.")
    title = "LETV-%s" % vu
    letvcloud_download_by_vu(
        vu, uu, title=title, output_dir=output_dir, merge=merge, info_only=info_only
    )


def letv_download(url, output_dir='.', merge=True, info_only=False, **kwargs):
    url = url_locations([url])[0]
    if re.match(r'http://yuntv.letv.com/', url):
        letvcloud_download(url, output_dir=output_dir, merge=merge, info_only=info_only)
    elif 'sports.le.com' in url:
        html = get_content(url)
        vid = match1(url, r'video/(\d+)\.html')
        title = match1(html, r'<h2 class="title">([^<]+)</h2>')
        letv_download_by_vid(vid, title=title, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)
    else:
        html = get_content(url)
        vid = match1(url, r'http://www.letv.com/ptv/vplay/(\d+).html') or \
              match1(url, r'http://www.le.com/ptv/vplay/(\d+).html') or \
              match1(html, r'vid="(\d+)"')
        title = match1(html, r'name="irTitle" content="(.*?)"')
        letv_download_by_vid(vid, title=title, output_dir=output_dir, merge=merge, info_only=info_only, **kwargs)


site_info = "Le.com"
download = letv_download
download_playlist = playlist_not_supported('letv')
