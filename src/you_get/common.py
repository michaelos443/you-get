#!/usr/bin/env python

import io
import os
import re
import sys
import time
import json
import socket
import locale
import logging
import argparse
import ssl
import sqlite3
import shutil
import tempfile
import http.client
from typing import List, Tuple, Any, Dict, Optional, Callable
from http.cookiejar import Cookie, MozillaCookieJar
from importlib import import_module
from types import ModuleType
from urllib import request, parse, error
from urllib.error import HTTPError, URLError

from .version import __version__
from .util import log, term
from .util.git import get_version
from .util.strings import get_filename, unescape_html
from . import json_output as json_output_

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf8')

RC4_STATE_SIZE = 256

SITES = {
    '163'              : 'netease',
    '56'               : 'w56',
    '365yg'            : 'toutiao',
    'acfun'            : 'acfun',
    'archive'          : 'archive',
    'baidu'            : 'baidu',
    'bandcamp'         : 'bandcamp',
    'baomihua'         : 'baomihua',
    'bigthink'         : 'bigthink',
    'bilibili'         : 'bilibili',
    'cctv'             : 'cntv',
    'cntv'             : 'cntv',
    'cbs'              : 'cbs',
    'coub'             : 'coub',
    'dailymotion'      : 'dailymotion',
    'douban'           : 'douban',
    'douyin'           : 'douyin',
    'douyu'            : 'douyutv',
    'ehow'             : 'ehow',
    'facebook'         : 'facebook',
    'fc2'              : 'fc2video',
    'flickr'           : 'flickr',
    'freesound'        : 'freesound',
    'fun'              : 'funshion',
    'google'           : 'google',
    'giphy'            : 'giphy',
    'heavy-music'      : 'heavymusic',
    'huomao'           : 'huomaotv',
    'iask'             : 'sina',
    'icourses'         : 'icourses',
    'ifeng'            : 'ifeng',
    'imgur'            : 'imgur',
    'in'               : 'alive',
    'infoq'            : 'infoq',
    'instagram'        : 'instagram',
    'interest'         : 'interest',
    'iqilu'            : 'iqilu',
    'iqiyi'            : 'iqiyi',
    'ixigua'           : 'ixigua',
    'isuntv'           : 'suntv',
    'iwara'            : 'iwara',
    'joy'              : 'joy',
    'kankanews'        : 'bilibili',
    'kakao'            : 'kakao',
    'khanacademy'      : 'khan',
    'ku6'              : 'ku6',
    'kuaishou'         : 'kuaishou',
    'kugou'            : 'kugou',
    'kuwo'             : 'kuwo',
    'le'               : 'le',
    'letv'             : 'le',
    'lizhi'            : 'lizhi',
    'longzhu'          : 'longzhu',
    'lrts'             : 'lrts',
    'magisto'          : 'magisto',
    'metacafe'         : 'metacafe',
    'mgtv'             : 'mgtv',
    'miomio'           : 'miomio',
    'missevan'         : 'missevan',
    'mixcloud'         : 'mixcloud',
    'mtv81'            : 'mtv81',
    'miaopai'          : 'yixia',
    'naver'            : 'naver',
    '7gogo'            : 'nanagogo',
    'nicovideo'        : 'nicovideo',
    'pinterest'        : 'pinterest',
    'pixnet'           : 'pixnet',
    'pptv'             : 'pptv',
    'qingting'         : 'qingting',
    'qq'               : 'qq',
    'showroom-live'    : 'showroom',
    'sina'             : 'sina',
    'smgbb'            : 'bilibili',
    'sohu'             : 'sohu',
    'soundcloud'       : 'soundcloud',
    'ted'              : 'ted',
    'theplatform'      : 'theplatform',
    'tiktok'           : 'tiktok',
    'tucao'            : 'tucao',
    'tudou'            : 'tudou',
    'tumblr'           : 'tumblr',
    'twimg'            : 'twitter',
    'twitter'          : 'twitter',
    'ucas'             : 'ucas',
    'vimeo'            : 'vimeo',
    'wanmen'           : 'wanmen',
    'weibo'            : 'miaopai',
    'veoh'             : 'veoh',
    'vk'               : 'vk',
    'x'                : 'twitter',
    'xiaokaxiu'        : 'yixia',
    'xiaojiadianvideo' : 'fc2video',
    'ximalaya'         : 'ximalaya',
    'xinpianchang'     : 'xinpianchang',
    'yizhibo'          : 'yizhibo',
    'youku'            : 'youku',
    'youtu'            : 'youtube',
    'youtube'          : 'youtube',
    'zhanqi'           : 'zhanqi',
    'zhibo'            : 'zhibo',
    'zhihu'            : 'zhihu',
}

dry_run = False
json_output = False
force = False
skip_existing_file_size_check = False
player = None
extractor_proxy = None
cookies = None
output_filename = None
auto_rename = False
insecure = False
m3u8 = False
postfix = False
prefix = None
enhanced_progress = False

fake_headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'UTF-8,*;q=0.5',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'en-US,en;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/126.0.2592.113'  # Latest Edge
}

if sys.stdout.isatty():
    default_encoding = sys.stdout.encoding.lower()
else:
    default_encoding = locale.getpreferredencoding().lower()


def rc4(key: bytes, data: bytes) -> bytes:
    """
    RC4 Encryption/Decryption algorithm implementation.

    This function implements the RC4 stream cipher algorithm, which is a symmetric-key algorithm
    that uses a variable-length key and generates a pseudo-random stream of bits (the key stream),
    which is then XORed with the plaintext (or ciphertext) to produce the encrypted (or decrypted) output.

    Args:
        key (bytes): The secret key used for encryption/decryption.
        data (bytes): The input data to be encrypted/decrypted.

    Returns:
        bytes: The encrypted/decrypted output.
    """
    # Ensure both key and data are byte strings.
    assert isinstance(key, bytes) and isinstance(data, bytes), "Both key and data must be byte strings"
    # Initialize state array with values from 0 to 255.
    state = list(range(RC4_STATE_SIZE))
    # Generate the key stream by shuffling the state array.
    j = 0
    for i in range(RC4_STATE_SIZE):
        j += state[i] + key[i % len(key)]
        j &= 0xff
        state[i], state[j] = state[j], state[i]

    # Generate the encrypted/decrypted output by XORing the key stream with the input data.
    i, j = 0, 0
    output = bytearray()
    for char in data:
        i += 1
        i &= 0xff
        j += state[i]
        j &= 0xff
        state[i], state[j] = state[j], state[i]
        prn = state[(state[i] + state[j]) & 0xff]
        output.append(char ^ prn)

    return output


def general_m3u8_extractor(url: str, headers: dict = {}) -> List[str]:
    """
    Extracts and returns a list of URLs from an M3U8 playlist.

    This function fetches the content of the provided M3U8 URL, parses it,
    and returns a list of URLs from the playlist.

    Args:
        url (str): The URL of the M3U8 playlist.
        headers (dict, optional): Additional HTTP headers to send with the request.

    Returns:
        List[str]: A list of URLs from the M3U8 playlist.
    """
    m3u8_list = get_content(url, headers=headers).split('\n')
    urls = [
        parse.urljoin(url, line) if not line.startswith("http") else line
        for line in m3u8_list if line.strip() and not line.startswith("#")
    ]
    return urls


def maybe_print(*s: Any) -> None:
    try:
        print(*s)
    except:
        pass


def tr(s):
    if default_encoding == 'utf-8':
        return s
    else:
        return s
        # return str(s.encode('utf-8'))[2:-1]


# DEPRECATED in favor of match1()
def r1(pattern, text):
    """Searches for a single match of a regex pattern within text.

    Args:
        pattern: Regular expression pattern to search for.
        text: Text in which to search for the pattern.

    Returns:
        The matched substring, or None if no match is found.
    """
    m = re.search(pattern, text)
    if m:
        return m.group(1)


# DEPRECATED in favor of match1()
def r1_of(patterns, text):
    return next((r1(p, text) for p in patterns if r1(p, text)), None)


def match1(text, *patterns):
    """Scans through a string for substrings matched some patterns (first-subgroups only).

    Args:
        text: A string to be scanned.
        patterns: Arbitrary number of regex patterns.

    Returns:
        When only one pattern is given, returns a string (None if no match found).
        When more than one pattern are given, returns a list of strings ([] if no match found).
    """
    match = re.search(patterns[0], text) if len(patterns) == 1 else [re.search(p, text) for p in patterns]
    return match[0].group(1) if match[0] else None


def matchall(text, patterns):
    """Scans through a string for substrings matched some patterns.

    Args:
        text: A string to be scanned.
        patterns: a list of regex pattern.

    Returns:
        a list if matched. empty if not.
    """

    ret = []
    for pattern in patterns:
        match = re.findall(pattern, text)
        ret += match

    return ret


def launch_player(player, urls):
    """
    Launches a media player with the given URLs.

    This function takes a media player command (player) and a list of URLs (urls) as input.
    It ensures that any nested lists of URLs are flattened and validates that all URLs are strings.
    It then attempts to execute the media player with the provided URLs. If the system is running
    Python 3.3 or later, it checks if the media player executable is available on the system.
    If the executable is not found, an error message is logged.

    Parameters:
    player (str): The command or path to the media player executable to launch.
    urls (iterable): A list or other iterable containing URLs or file paths to be opened by the media player.
                     Nested lists of URLs are flattened into a single list.

    Raises:
    AssertionError: If no valid URLs are provided.
    """
    import subprocess
    import shlex
    urls = list(urls)
    for url in urls.copy():
        if type(url) is list:
            urls.extend(url)
    urls = [url for url in urls if type(url) is str]
    assert urls
    if (sys.version_info >= (3, 3)):
        import shutil
        exefile=shlex.split(player)[0]
        if shutil.which(exefile) is not None:
            subprocess.call(shlex.split(player) + urls)
        else:
            log.wtf('[Failed] Cannot find player "%s"' % exefile)
    else:
        subprocess.call(shlex.split(player) + urls)


def parse_query_param(url: str, param):
    """Parses the query string of a URL and returns the value of a parameter.

    Args:
        url: A URL.
        param: A string representing the name of the parameter.

    Returns:
        The value of the parameter.
    """

    try:
        return parse.parse_qs(parse.urlparse(url).query)[param][0]
    except Exception:
        return None


def unicodize(text):
    return re.sub(
        r'\\u([0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f][0-9A-Fa-f])',
        lambda x: chr(int(x.group(0)[2:], 16)),
        text
    )


# DEPRECATED in favor of util.legitimize()
def escape_file_path(path):
    path = path.replace('/', '-')
    path = path.replace('\\', '-')
    path = path.replace('*', '-')
    path = path.replace('?', '-')
    return path


def ungzip(data: bytes) -> bytes:
    """Decompresses data for Content-Encoding: gzip.
    """
    from io import BytesIO
    import gzip
    buffer = BytesIO(data)  # type: ignore
    with gzip.GzipFile(fileobj=buffer) as f:
        return f.read()


def undeflate(data: bytes) -> bytes:
    """Decompresses data for Content-Encoding: deflate.
    (the zlib compression is used.)
    """
    import zlib
    decompressobj = zlib.decompressobj(-zlib.MAX_WBITS)  # type: ignore
    return decompressobj.decompress(data)+decompressobj.flush()


# an http.client implementation of get_content()
# because urllib does not support "Connection: keep-alive"
def getHttps(host, url, headers, debuglevel=0):
    import http.client

    conn = http.client.HTTPSConnection(host)
    conn.set_debuglevel(debuglevel)
    conn.request("GET", url, headers=headers)
    resp = conn.getresponse()
    logging.debug('getHttps: %s' % resp.getheaders())
    set_cookie = resp.getheader('set-cookie')

    data = resp.read()
    try:
        data = ungzip(data)  # gzip
        data = undeflate(data)  # deflate
    except:
        pass

    conn.close()
    return str(data, encoding='utf-8'), set_cookie  # TODO: support raw data


# DEPRECATED in favor of get_content()
def get_response(url, faker=False):
    logging.debug('get_response: %s' % url)
    ctx = None
    if insecure:
        # ignore ssl errors
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    # install cookies
    if cookies:
        opener = request.build_opener(request.HTTPCookieProcessor(cookies))
        request.install_opener(opener)

    if faker:
        response = request.urlopen(
            request.Request(url, headers=fake_headers), None, context=ctx,
        )
    else:
        response = request.urlopen(url, context=ctx)

    data = response.read()
    if response.info().get('Content-Encoding') == 'gzip':
        data = ungzip(data)
    elif response.info().get('Content-Encoding') == 'deflate':
        data = undeflate(data)
    response.data = data
    return response


# DEPRECATED in favor of get_content()
def get_html(url, encoding=None, faker=False):
    content = get_response(url, faker).data
    return str(content, 'utf-8', 'ignore')


# DEPRECATED in favor of get_content()
def get_decoded_html(url, faker=False):
    response = get_response(url, faker)
    data = response.data
    charset = r1(r'charset=([\w-]+)', response.headers['content-type'])
    if charset:
        return data.decode(charset, 'ignore')
    else:
        return data


def get_location(
        url: str, headers: Optional[dict] = None,
        get_method: str = 'HEAD') -> Optional[str]:
    """
    Attempts to retrieve the final URL after following any redirects.

    This function sends a request to the provided URL with the specified HTTP method
    (default is 'HEAD'). potentially using custom headers, and returns the final URL.
    If an error occurs, it returns None.

    Args:
        url (str): The URL to retrieve.
        headers (Optional[dict], optional): Custom headers to use for the request.
        get_method (str, optional): The HTTP method to use for the request.

    Returns:
        Optional[str]: The final URL after following any redirects, or None if an error occurs.
    """
    logging.debug('get_location: %s' % url)
    try:
        # Create a request object with optional headers.
        req = request.Request(url, headers=headers or {})
        req.get_method = lambda: get_method
        res = urlopen_with_retry(req)
        return res.geturl()
    except HTTPError as e:
        logging.debug(f"get_location: {e}")
        return None
    except URLError as e:
        logging.debug(f"get_location: {e}")
        return None


def urlopen_with_retry(
        *args: Any, **kwargs: Dict[str, Any]) -> http.client.HTTPResponse:
    retry_time = 3
    for i in range(retry_time):
        try:
            if insecure:
                # ignore ssl errors
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                return request.urlopen(*args, context=ctx, **kwargs)
            else:
                return request.urlopen(*args, **kwargs)
        except socket.timeout as e:
            logging.debug('request attempt %s timeout' % str(i + 1))
            if i + 1 == retry_time:
                raise e
        # try to tackle youku CDN fails
        except error.HTTPError as http_error:
            logging.debug('HTTP Error with code{}'.format(http_error.code))
            if i + 1 == retry_time:
                raise http_error


def get_content(url, headers={}, decoded=True):
    """Gets the content of a URL via sending a HTTP GET request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """

    logging.debug('get_content: %s' % url)

    req = request.Request(url, headers=headers)
    if cookies:
        # NOTE: Do not use cookies.add_cookie_header(req)
        # #HttpOnly_ cookies were not supported by CookieJar and MozillaCookieJar properly until python 3.10
        # See also:
        # - https://github.com/python/cpython/pull/17471
        # - https://bugs.python.org/issue2190
        # Here we add cookies to the request headers manually
        cookie_strings = []
        for cookie in list(cookies):
            cookie_strings.append(cookie.name + '=' + cookie.value)
        cookie_headers = {'Cookie': '; '.join(cookie_strings)}
        req.headers.update(cookie_headers)

    response = urlopen_with_retry(req)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.getheader('Content-Encoding')
    if content_encoding == 'gzip':
        data = ungzip(data)
    elif content_encoding == 'deflate':
        data = undeflate(data)

    # Decode the response body
    if decoded:
        charset = match1(
            response.getheader('Content-Type', ''), r'charset=([\w-]+)'
        )
        if charset is not None:
            data = data.decode(charset, 'ignore')
        else:
            data = data.decode('utf-8', 'ignore')

    return data


def post_content(url, headers={}, post_data={}, decoded=True, **kwargs):
    """Post the content of a URL via sending a HTTP POST request.

    Args:
        url: A URL.
        headers: Request headers used by the client.
        decoded: Whether decode the response body using UTF-8 or the charset specified in Content-Type.

    Returns:
        The content as a string.
    """
    if kwargs.get('post_data_raw'):
        logging.debug('post_content: %s\npost_data_raw: %s' % (url, kwargs['post_data_raw']))
    else:
        logging.debug('post_content: %s\npost_data: %s' % (url, post_data))

    req = request.Request(url, headers=headers)
    if cookies:
        # NOTE: Do not use cookies.add_cookie_header(req)
        # #HttpOnly_ cookies were not supported by CookieJar and MozillaCookieJar properly until python 3.10
        # See also:
        # - https://github.com/python/cpython/pull/17471
        # - https://bugs.python.org/issue2190
        # Here we add cookies to the request headers manually
        cookie_strings = []
        for cookie in list(cookies):
            cookie_strings.append(cookie.name + '=' + cookie.value)
        cookie_headers = {'Cookie': '; '.join(cookie_strings)}
        req.headers.update(cookie_headers)
    if kwargs.get('post_data_raw'):
        post_data_enc = bytes(kwargs['post_data_raw'], 'utf-8')
    else:
        post_data_enc = bytes(parse.urlencode(post_data), 'utf-8')
    response = urlopen_with_retry(req, data=post_data_enc)
    data = response.read()

    # Handle HTTP compression for gzip and deflate (zlib)
    content_encoding = response.getheader('Content-Encoding')
    if content_encoding == 'gzip':
        data = ungzip(data)
    elif content_encoding == 'deflate':
        data = undeflate(data)

    # Decode the response body
    if decoded:
        charset = match1(
            response.getheader('Content-Type'), r'charset=([\w-]+)'
        )
        if charset is not None:
            data = data.decode(charset)
        else:
            data = data.decode('utf-8')

    return data


def url_size(url, faker=False, headers={}):
    if faker:
        response = urlopen_with_retry(
            request.Request(url, headers=fake_headers)
        )
    elif headers:
        response = urlopen_with_retry(request.Request(url, headers=headers))
    else:
        response = urlopen_with_retry(url)

    size = response.headers['content-length']
    return int(size) if size is not None else float('inf')


def urls_size(urls, faker=False, headers={}):
    return sum([url_size(url, faker=faker, headers=headers) for url in urls])


def get_head(url, headers=None, get_method='HEAD'):
    logging.debug('get_head: %s' % url)

    if headers:
        req = request.Request(url, headers=headers)
    else:
        req = request.Request(url)
    req.get_method = lambda: get_method
    res = urlopen_with_retry(req)
    return res.headers


def url_info(url, faker=False, headers={}):
    logging.debug('url_info: %s' % url)

    if faker:
        response = urlopen_with_retry(
            request.Request(url, headers=fake_headers)
        )
    elif headers:
        response = urlopen_with_retry(request.Request(url, headers=headers))
    else:
        response = urlopen_with_retry(request.Request(url))

    headers = response.headers

    type = headers['content-type']
    if type == 'image/jpg; charset=UTF-8' or type == 'image/jpg':
        type = 'audio/mpeg'  # fix for netease
    mapping = {
        'video/3gpp': '3gp',
        'video/f4v': 'flv',
        'video/mp4': 'mp4',
        'video/MP2T': 'ts',
        'video/quicktime': 'mov',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
        'video/x-ms-asf': 'asf',
        'audio/mp4': 'mp4',
        'audio/mpeg': 'mp3',
        'audio/wav': 'wav',
        'audio/x-wav': 'wav',
        'audio/wave': 'wav',
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'application/pdf': 'pdf',
    }
    if type in mapping:
        ext = mapping[type]
    else:
        type = None
        if headers['content-disposition']:
            try:
                filename = parse.unquote(
                    r1(r'filename="?([^"]+)"?', headers['content-disposition'])
                )
                if len(filename.split('.')) > 1:
                    ext = filename.split('.')[-1]
                else:
                    ext = None
            except:
                ext = None
        else:
            ext = None

    if headers['transfer-encoding'] != 'chunked':
        size = headers['content-length'] and int(headers['content-length'])
    else:
        size = None

    return type, ext, size


def url_locations(urls, faker=False, headers={}):
    locations = []
    for url in urls:
        logging.debug('url_locations: %s' % url)

        if faker:
            response = urlopen_with_retry(
                request.Request(url, headers=fake_headers)
            )
        elif headers:
            response = urlopen_with_retry(
                request.Request(url, headers=headers)
            )
        else:
            response = urlopen_with_retry(request.Request(url))

        locations.append(response.url)
    return locations


def url_save(
    url, filepath, bar, refer=None, is_part=False, faker=False,
    headers=None, timeout=None, **kwargs
):
    tmp_headers = headers.copy() if headers is not None else {}
    # When a referer specified with param refer,
    # the key must be 'Referer' for the hack here
    if refer is not None:
        tmp_headers['Referer'] = refer
    if type(url) is list:
        chunk_sizes = [url_size(url, faker=faker, headers=tmp_headers) for url in url]
        file_size = sum(chunk_sizes)
        is_chunked, urls = True, url
    else:
        file_size = url_size(url, faker=faker, headers=tmp_headers)
        chunk_sizes = [file_size]
        is_chunked, urls = False, [url]

    continue_renameing = True
    while continue_renameing:
        continue_renameing = False
        if os.path.exists(filepath):
            if not force and (file_size == os.path.getsize(filepath) or skip_existing_file_size_check):
                if not is_part:
                    if bar:
                        bar.done()
                    if skip_existing_file_size_check:
                        log.w(
                            'Skipping {} without checking size: file already exists'.format(
                                tr(os.path.basename(filepath))
                            )
                        )
                    else:
                        log.w(
                            'Skipping {}: file already exists'.format(
                                tr(os.path.basename(filepath))
                            )
                        )
                else:
                    if bar:
                        bar.update_received(file_size)
                return
            else:
                if not is_part:
                    if bar:
                        bar.done()
                    if not force and auto_rename:
                        path, ext = os.path.basename(filepath).rsplit('.', 1)
                        finder = re.compile(r' \([1-9]\d*?\)$')
                        if (finder.search(path) is None):
                            thisfile = path + ' (1).' + ext
                        else:
                            def numreturn(a):
                                return ' (' + str(int(a.group()[2:-1]) + 1) + ').'
                            thisfile = finder.sub(numreturn, path) + ext
                        filepath = os.path.join(os.path.dirname(filepath), thisfile)
                        print('Changing name to %s' % tr(os.path.basename(filepath)), '...')
                        continue_renameing = True
                        continue
                    if log.yes_or_no('File with this name already exists. Overwrite?'):
                        log.w('Overwriting %s ...' % tr(os.path.basename(filepath)))
                    else:
                        return
        elif not os.path.exists(os.path.dirname(filepath)):
            os.mkdir(os.path.dirname(filepath))

    temp_filepath = filepath + '.download' if file_size != float('inf') \
        else filepath
    received = 0
    if not force:
        open_mode = 'ab'

        if os.path.exists(temp_filepath):
            received += os.path.getsize(temp_filepath)
            if bar:
                bar.update_received(os.path.getsize(temp_filepath))
    else:
        open_mode = 'wb'

    chunk_start = 0
    chunk_end = 0
    for i, url in enumerate(urls):
        received_chunk = 0
        chunk_start += 0 if i == 0 else chunk_sizes[i - 1]
        chunk_end += chunk_sizes[i]
        if received < file_size and received < chunk_end:
            if faker:
                tmp_headers = fake_headers
            '''
            if parameter headers passed in, we have it copied as tmp_header
            elif headers:
                headers = headers
            else:
                headers = {}
            '''
            if received:
                # chunk_start will always be 0 if not chunked
                tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
            if refer:
                tmp_headers['Referer'] = refer

            if timeout:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers), timeout=timeout
                )
            else:
                response = urlopen_with_retry(
                    request.Request(url, headers=tmp_headers)
                )
            try:
                range_start = int(
                    response.headers[
                        'content-range'
                    ][6:].split('/')[0].split('-')[0]
                )
                end_length = int(
                    response.headers['content-range'][6:].split('/')[1]
                )
                range_length = end_length - range_start
            except:
                content_length = response.headers['content-length']
                range_length = int(content_length) if content_length is not None \
                    else float('inf')

            if is_chunked:  # always append if chunked
                open_mode = 'ab'
            elif file_size != received + range_length:  # is it ever necessary?
                received = 0
                if bar:
                    bar.received = 0
                open_mode = 'wb'

            with open(temp_filepath, open_mode) as output:
                while True:
                    buffer = None
                    try:
                        buffer = response.read(1024 * 256)
                    except socket.timeout:
                        pass
                    if not buffer:
                        if is_chunked and received_chunk == range_length:
                            break
                        elif not is_chunked and received == file_size:  # Download finished
                            break
                        # Unexpected termination. Retry request
                        tmp_headers['Range'] = 'bytes=' + str(received - chunk_start) + '-'
                        response = urlopen_with_retry(
                            request.Request(url, headers=tmp_headers)
                        )
                        continue
                    output.write(buffer)
                    received += len(buffer)
                    received_chunk += len(buffer)
                    if bar:
                        bar.update_received(len(buffer))

    assert received == os.path.getsize(temp_filepath), '%s == %s == %s' % (
        received, os.path.getsize(temp_filepath), temp_filepath
    )

    if os.access(filepath, os.W_OK):
        # on Windows rename could fail if destination filepath exists
        os.remove(filepath)
    os.rename(temp_filepath, filepath)


class SimpleProgressBar:
    """
    A simple progress bar for displaying the progress of a download operation.

    This class provides a simple progress bar for displaying the progress of a download operation.
    It displays the current progress as a percentage, the current speed, and the current piece number.
    """

    term_size = term.get_terminal_size()[1]

    def __init__(
        self,
        total_size: int,
        total_pieces: int = 1
    ) -> None:
        """
        Initializes a new SimpleProgressBar instance.

        Args:
            total_size (int): The total size of the download operation.
            total_pieces (int, optional): The total number of pieces in the download operation.
        """
        self.displayed = False
        self.total_size = total_size
        self.total_pieces = total_pieces
        self.current_piece = 1
        self.received = 0
        self.speed = ''
        self.last_updated = time.time()
        self.start_time = time.time()
        self.speed_samples = []  # For better speed calculation

        total_pieces_len = len(str(total_pieces))
        # 38 is the size of all statically known size in self.bar
        total_str = '%5s' % round(self.total_size / 1048576, 1)
        total_str_width = max(len(total_str), 5)
        self.bar_size = self.term_size - 28 - 2 * total_pieces_len \
            - 2 * total_str_width
        self.bar = '{:>4}%% ({:>%s}/%sMB) ├{:─<%s}┤[{:>%s}/{:>%s}] {}' % (
            total_str_width, total_str, self.bar_size, total_pieces_len,
            total_pieces_len
        )

    def update(
        self
    ):
        self.displayed = True
        bar_size = self.bar_size
        percent = round(self.received * 100 / self.total_size, 1)
        if percent >= 100:
            percent = 100
        dots = bar_size * int(percent) // 100
        plus = int(percent) - dots // bar_size * 100
        if plus > 0.8:
            plus = '█'
        elif plus > 0.4:
            plus = '>'
        else:
            plus = ''
        bar = '█' * dots + plus
        bar = self.bar.format(
            percent, round(self.received / 1048576, 1), bar,
            self.current_piece, self.total_pieces, self.speed
        )
        sys.stdout.write('\r' + bar)
        sys.stdout.flush()

    def update_received(self, n: int) -> None:
        self.received += n
        current_time = time.time()
        time_diff = current_time - self.last_updated

        # Calculate instantaneous speed
        bytes_ps = n / time_diff if time_diff > 0 else 0

        # Keep a rolling average of speed samples for better ETA calculation
        if bytes_ps > 0:
            self.speed_samples.append(bytes_ps)
            # Keep only last 10 samples for rolling average
            if len(self.speed_samples) > 10:
                self.speed_samples.pop(0)

        # Use average speed for more stable display
        avg_speed = sum(self.speed_samples) / len(self.speed_samples) if self.speed_samples else 0

        # Format speed display
        if avg_speed >= 1024 ** 3:
            self.speed = '{:4.0f} GB/s'.format(avg_speed / 1024 ** 3)
        elif avg_speed >= 1024 ** 2:
            self.speed = '{:4.0f} MB/s'.format(avg_speed / 1024 ** 2)
        elif avg_speed >= 1024:
            self.speed = '{:4.0f} kB/s'.format(avg_speed / 1024)
        else:
            self.speed = '{:4.0f}  B/s'.format(avg_speed)

        self.last_updated = current_time
        self.update()

    def update_piece(self, n: int) -> None:
        self.current_piece = n

    def done(self) -> None:
        if self.displayed:
            print()
            self.displayed = False


class EnhancedProgressBar:
    """
    Enhanced progress bar with ETA, better formatting, and detailed statistics.
    Features:
    - Rolling average speed calculation with trend analysis
    - Adaptive progress bar width
    - Human-readable time and size formatting
    - ETA calculation with improved accuracy and prediction tracking
    - Visual progress indicators with Unicode characters
    - Bandwidth utilization metrics (peak/average speeds)
    - Speed trend indicators (↑/↓/→)
    - Network interruption handling
    - Configurable update frequency and display elements
    """

    term_size = term.get_terminal_size()[1]

    def __init__(self, total_size: int, total_pieces: int = 1) -> None:
        self.displayed = False
        self.total_size = total_size
        self.total_pieces = total_pieces
        self.current_piece = 1
        self.received = 0
        self.start_time = time.time()
        self.last_updated = time.time()
        self.speed_samples = []  # Store (timestamp, bytes_received) tuples
        self.max_speed_samples = 15  # Keep last 15 samples for rolling average

        # Enhanced metrics
        self.peak_speed = 0.0
        self.speed_trend = "→"  # ↑ increasing, ↓ decreasing, → stable
        self.eta_predictions = []  # Track ETA accuracy over time
        self.stall_count = 0  # Count consecutive low-speed periods
        self.last_trend_check = time.time()
        self.update_frequency = 0.1  # Update every 100ms

    def _format_time(self, seconds: float) -> str:
        """Format time in human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m{int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h{minutes}m"

    def _format_size(self, size: int) -> str:
        """Format file size in human readable format."""
        if size >= 1024 ** 3:
            return f"{size / (1024 ** 3):.1f}GB"
        elif size >= 1024 ** 2:
            return f"{size / (1024 ** 2):.1f}MB"
        elif size >= 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size}B"

    def _calculate_rolling_speed(self) -> float:
        """Calculate speed using rolling average of recent samples with trend analysis."""
        current_time = time.time()

        # Add current sample
        self.speed_samples.append((current_time, self.received))

        # Keep only recent samples (last 10 seconds or max_speed_samples)
        cutoff_time = current_time - 10.0  # 10 seconds window
        self.speed_samples = [
            (t, r) for t, r in self.speed_samples
            if t > cutoff_time
        ][-self.max_speed_samples:]

        if len(self.speed_samples) < 2:
            return 0.0

        # Calculate speed from first to last sample
        time_diff = self.speed_samples[-1][0] - self.speed_samples[0][0]
        bytes_diff = self.speed_samples[-1][1] - self.speed_samples[0][1]

        current_speed = bytes_diff / time_diff if time_diff > 0 else 0.0

        # Update peak speed
        if current_speed > self.peak_speed:
            self.peak_speed = current_speed

        # Update speed trend (check every 2 seconds)
        if current_time - self.last_trend_check >= 2.0 and len(self.speed_samples) >= 6:
            self._update_speed_trend()
            self.last_trend_check = current_time

        # Detect stalls (speed < 1KB/s for extended period)
        if current_speed < 1024:  # Less than 1KB/s
            self.stall_count += 1
        else:
            self.stall_count = 0

        return current_speed

    def _update_speed_trend(self) -> None:
        """Update speed trend indicator based on recent samples."""
        if len(self.speed_samples) < 6:
            return

        # Compare recent speeds (last 3 samples vs previous 3)
        mid_point = len(self.speed_samples) // 2
        recent_samples = self.speed_samples[mid_point:]
        older_samples = self.speed_samples[:mid_point]

        if len(recent_samples) >= 2 and len(older_samples) >= 2:
            recent_speed = (recent_samples[-1][1] - recent_samples[0][1]) / (recent_samples[-1][0] - recent_samples[0][0])
            older_speed = (older_samples[-1][1] - older_samples[0][1]) / (older_samples[-1][0] - older_samples[0][0])

            speed_diff = recent_speed - older_speed
            threshold = older_speed * 0.1  # 10% change threshold

            if speed_diff > threshold:
                self.speed_trend = "↑"
            elif speed_diff < -threshold:
                self.speed_trend = "↓"
            else:
                self.speed_trend = "→"

    def _track_eta_accuracy(self, eta_seconds: float) -> None:
        """Track ETA prediction accuracy for learning."""
        current_time = time.time()
        self.eta_predictions.append((current_time, eta_seconds, self.received))

        # Keep only recent predictions (last 30 seconds)
        cutoff_time = current_time - 30.0
        self.eta_predictions = [
            (t, eta, received) for t, eta, received in self.eta_predictions
            if t > cutoff_time
        ]

    def update(self) -> None:
        self.displayed = True
        current_time = time.time()
        elapsed = current_time - self.start_time

        # Calculate progress percentage
        percent = (self.received / self.total_size * 100) if self.total_size > 0 else 0

        # Calculate rolling average speed for better accuracy
        rolling_speed = self._calculate_rolling_speed()

        # Fallback to overall average if rolling speed is 0
        avg_speed = rolling_speed if rolling_speed > 0 else (self.received / elapsed if elapsed > 0 else 0)

        # Calculate ETA with improved accuracy
        remaining_bytes = self.total_size - self.received
        eta_seconds = remaining_bytes / avg_speed if avg_speed > 0 else 0

        # Track ETA accuracy
        if eta_seconds > 0:
            self._track_eta_accuracy(eta_seconds)

        # Format components with enhanced precision and metrics
        percent_str = f"{percent:5.1f}%"
        received_str = self._format_size(self.received)
        total_str = self._format_size(self.total_size)

        # Enhanced speed display with trend and peak info
        speed_str = f"{self._format_size(avg_speed)}/s{self.speed_trend}" if avg_speed > 0 else "0B/s→"
        peak_str = f"↑{self._format_size(self.peak_speed)}/s" if self.peak_speed > avg_speed * 1.2 else ""

        # Enhanced ETA with stall detection
        if self.stall_count > 5:  # Stalled for more than 5 updates
            eta_str = "⚠STALL"
        elif eta_seconds > 0 and percent < 99.9:
            eta_str = self._format_time(eta_seconds)
        else:
            eta_str = "✓"

        elapsed_str = self._format_time(elapsed)

        # Create enhanced progress bar with better visual indicators
        bar_width = max(20, self.term_size - 100)  # More space for enhanced metrics
        filled_width = int(bar_width * percent / 100)

        # Use different characters for different completion levels
        if percent >= 100:
            bar = "█" * bar_width
        else:
            # Add partial character for more precise visual feedback
            partial_char = ""
            partial_progress = (bar_width * percent / 100) - filled_width
            if partial_progress > 0.7:
                partial_char = "▉"
            elif partial_progress > 0.5:
                partial_char = "▊"
            elif partial_progress > 0.3:
                partial_char = "▋"
            elif partial_progress > 0.1:
                partial_char = "▌"

            bar = "█" * filled_width + partial_char + "░" * (bar_width - filled_width - len(partial_char))

        # Format final display with enhanced layout and metrics
        if self.total_pieces > 1:
            display = f"\r{percent_str} [{bar}] {received_str}/{total_str} {speed_str} {peak_str} ETA:{eta_str} Part:[{self.current_piece}/{self.total_pieces}]"
        else:
            display = f"\r{percent_str} [{bar}] {received_str}/{total_str} {speed_str} {peak_str} ETA:{eta_str} T:{elapsed_str}"

        # Truncate if too long
        if len(display) > self.term_size:
            display = display[:self.term_size-3] + "..."

        sys.stdout.write(display)
        sys.stdout.flush()

    def update_received(self, n: int) -> None:
        self.received += n
        current_time = time.time()
        self.last_updated = current_time

        # Use configurable update frequency to avoid flickering
        if not hasattr(self, '_last_display_update'):
            self._last_display_update = 0

        if current_time - self._last_display_update >= self.update_frequency:
            self.update()
            self._last_display_update = current_time

    def update_piece(self, n: int) -> None:
        self.current_piece = n
        self.update()

    def done(self) -> None:
        if self.displayed:
            print()
            self.displayed = False


class PiecesProgressBar:
    def __init__(self, total_size, total_pieces=1):
        self.displayed = False
        self.total_size = total_size
        self.total_pieces = total_pieces
        self.current_piece = 1
        self.received = 0

    def update(self):
        self.displayed = True
        bar = '{0:>5}%[{1:<40}] {2}/{3}'.format(
            '', '=' * 40, self.current_piece, self.total_pieces
        )
        sys.stdout.write('\r' + bar)
        sys.stdout.flush()

    def update_received(self, n):
        self.received += n
        self.update()

    def update_piece(self, n):
        self.current_piece = n

    def done(self):
        if self.displayed:
            print()
            self.displayed = False


class DummyProgressBar:
    def __init__(self, *args):
        pass

    def update_received(self, n):
        pass

    def update_piece(self, n):
        pass

    def done(self):
        pass


def get_output_filename(urls, title, ext, output_dir, merge, **kwargs) -> str:
    # lame hack for the --output-filename option
    global output_filename
    if output_filename:
        result = output_filename
        if kwargs.get('part', -1) >= 0:
            result = '%s[%02d]' % (result, kwargs.get('part'))
        if ext:
            result = '%s.%s' % (result, ext)
        return result

    merged_ext = ext
    if (len(urls) > 1) and merge:
        from .processor.ffmpeg import has_ffmpeg_installed
        if ext in ['flv', 'f4v']:
            if has_ffmpeg_installed():
                merged_ext = 'mp4'
            else:
                merged_ext = 'flv'
        elif ext == 'mp4':
            merged_ext = 'mp4'
        elif ext == 'ts':
            if has_ffmpeg_installed():
                merged_ext = 'mkv'
            else:
                merged_ext = 'ts'
    result = title
    if kwargs.get('part', -1) >= 0:
        result = '%s[%02d]' % (result, kwargs.get('part'))
    result = '%s.%s' % (result, merged_ext)
    return result.replace("'", "_")

def print_user_agent(faker: bool = False) -> None:
    """
    Print the user agent to the console.

    Args:
        faker (bool): Whether to use a fake user agent.
    """
    urllib_default_user_agent = 'Python-urllib/%d.%d' % sys.version_info[:2]
    user_agent = fake_headers['User-Agent'] if faker else urllib_default_user_agent
    print('User Agent: %s' % user_agent)


def download_urls(
    urls, title, ext, total_size, output_dir='.', refer=None, merge=True,
    faker=False, headers={}, **kwargs
) -> None:
    assert urls
    if json_output:
        json_output_.download_urls(
            urls=urls, title=title, ext=ext, total_size=total_size,
            refer=refer
        )
        return
    if dry_run:
        print_user_agent(faker=faker)
        try:
            print('Real URLs:\n%s' % '\n'.join(urls))
        except Exception:
            print('Real URLs:\n%s' % '\n'.join([j for i in urls for j in i]))
        return

    if player:
        launch_player(player, urls)
        return

    if not total_size:
        try:
            total_size = urls_size(urls, faker=faker, headers=headers)
        except Exception:
            import traceback
            traceback.print_exc(file=sys.stdout)
            pass

    title = tr(get_filename(title))
    if postfix and 'vid' in kwargs:
        title = f"{title} [{kwargs['vid']}]"
    if prefix is not None:
        title = f"[{prefix}] {title}"
    output_filename = get_output_filename(urls, title, ext, output_dir, merge)
    output_filepath = os.path.join(output_dir, output_filename)

    if total_size:
        if not force and os.path.exists(output_filepath) and not auto_rename\
                and (os.path.getsize(output_filepath) >= total_size * 0.9\
                or skip_existing_file_size_check):
            if skip_existing_file_size_check:
                log.w('Skipping %s without checking size: file already exists' % output_filepath)
            else:
                log.w('Skipping %s: file already exists' % output_filepath)
            print()
            return
        # Use enhanced progress bar if enabled
        if enhanced_progress:
            bar = EnhancedProgressBar(total_size, len(urls))
        else:
            bar = SimpleProgressBar(total_size, len(urls))
    else:
        bar = PiecesProgressBar(total_size, len(urls))

    if len(urls) == 1:
        url = urls[0]
        print('Downloading %s ...' % tr(output_filename))
        bar.update()
        url_save(
            url, output_filepath, bar, refer=refer, faker=faker,
            headers=headers, **kwargs
        )
        bar.done()
    else:
        parts = []
        print('Downloading %s ...' % tr(output_filename))
        bar.update()
        for i, url in enumerate(urls):
            output_filename_i = get_output_filename(urls, title, ext, output_dir, merge, part=i)
            output_filepath_i = os.path.join(output_dir, output_filename_i)
            parts.append(output_filepath_i)
            # print 'Downloading %s [%s/%s]...' % (tr(filename), i + 1, len(urls))
            bar.update_piece(i + 1)
            url_save(
                url, output_filepath_i, bar, refer=refer, is_part=True, faker=faker,
                headers=headers, **kwargs
            )
        bar.done()

        if not merge:
            print()
            return

        if 'av' in kwargs and kwargs['av']:
            from .processor.ffmpeg import has_ffmpeg_installed
            if has_ffmpeg_installed():
                from .processor.ffmpeg import ffmpeg_concat_av
                ret = ffmpeg_concat_av(parts, output_filepath, ext)
                print('Merged into %s' % output_filename)
                if ret == 0:
                    for part in parts:
                        os.remove(part)

        elif ext in ['flv', 'f4v']:
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_flv_to_mp4
                    ffmpeg_concat_flv_to_mp4(parts, output_filepath)
                else:
                    from .processor.join_flv import concat_flv
                    concat_flv(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'mp4':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_mp4_to_mp4
                    ffmpeg_concat_mp4_to_mp4(parts, output_filepath)
                else:
                    from .processor.join_mp4 import concat_mp4
                    concat_mp4(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'ts':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed():
                    from .processor.ffmpeg import ffmpeg_concat_ts_to_mkv
                    ffmpeg_concat_ts_to_mkv(parts, output_filepath)
                else:
                    from .processor.join_ts import concat_ts
                    concat_ts(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        elif ext == 'mp3':
            try:
                from .processor.ffmpeg import has_ffmpeg_installed

                assert has_ffmpeg_installed()
                from .processor.ffmpeg import ffmpeg_concat_mp3_to_mp3
                ffmpeg_concat_mp3_to_mp3(parts, output_filepath)
                print('Merged into %s' % output_filename)
            except:
                raise
            else:
                for part in parts:
                    os.remove(part)

        else:
            print("Can't merge %s files" % ext)

    print()


def download_rtmp_url(
    url: str,
    title: str,
    ext: str,
    params: Optional[dict] = None,
    total_size: int = 0,
    output_dir: str = '.',
    refer: str = None,
    merge: bool = True,
    faker: bool = False
):
    # Default empty dictionary for params if not provided.
    if params is None:
        params = {}
    if not url:
        raise ValueError("URL is empty")
    if dry_run:
        print_user_agent(faker=faker)
        print('Real URL:\n%s\n' % [url])
        if params.get('-y', False):  # None or unset -> False
            print('Real Playpath:\n%s\n' % [params.get('-y')])
        return

    # If player is provided, handle the stream.
    if player:
        from .processor.rtmpdump import play_rtmpdump_stream
        play_rtmpdump_stream(player, url, params)
        return

    # Otherwise, proceed with downloading.
    from .processor.rtmpdump import (
        has_rtmpdump_installed, download_rtmpdump_stream
    )
    if not has_rtmpdump_installed():
        raise RuntimeError("RTMPDump not installed. Please install it to proceed.")
    download_rtmpdump_stream(url,  title, ext, params, output_dir)


def download_url_ffmpeg(
    url, title, ext, params={}, total_size=0, output_dir='.', refer=None,
    merge=True, faker=False, stream=True
):
    assert url
    if dry_run:
        print_user_agent(faker=faker)
        print('Real URL:\n%s\n' % [url])
        if params.get('-y', False):  # None or unset ->False
            print('Real Playpath:\n%s\n' % [params.get('-y')])
        return

    if player:
        launch_player(player, [url])
        return

    from .processor.ffmpeg import has_ffmpeg_installed, ffmpeg_download_stream
    assert has_ffmpeg_installed(), 'FFmpeg not installed.'

    global output_filename
    if output_filename:
        dotPos = output_filename.rfind('.')
        if dotPos > 0:
            title = output_filename[:dotPos]
            ext = output_filename[dotPos+1:]
        else:
            title = output_filename

    title = tr(get_filename(title))

    ffmpeg_download_stream(url, title, ext, params, output_dir, stream=stream)


def playlist_not_supported(
    name: str
) -> Callable[..., None]:
    def f(*args, **kwargs):
        raise NotImplementedError('Playlist is not supported for ' + name)
    return f


def print_info(site_info: str, title: str, type: str, size: int, **kwargs: Any) -> None:
    if json_output:
        json_output_.print_info(
            site_info=site_info, title=title, type=type, size=size
        )
        return
    if type:
        type = type.lower()
    if type in ['3gp']:
        type = 'video/3gpp'
    elif type in ['asf', 'wmv']:
        type = 'video/x-ms-asf'
    elif type in ['flv', 'f4v']:
        type = 'video/x-flv'
    elif type in ['mkv']:
        type = 'video/x-matroska'
    elif type in ['mp3']:
        type = 'audio/mpeg'
    elif type in ['mp4']:
        type = 'video/mp4'
    elif type in ['mov']:
        type = 'video/quicktime'
    elif type in ['ts']:
        type = 'video/MP2T'
    elif type in ['webm']:
        type = 'video/webm'

    elif type in ['jpg']:
        type = 'image/jpeg'
    elif type in ['png']:
        type = 'image/png'
    elif type in ['gif']:
        type = 'image/gif'

    if type in ['video/3gpp']:
        type_info = '3GPP multimedia file (%s)' % type
    elif type in ['video/x-flv', 'video/f4v']:
        type_info = 'Flash video (%s)' % type
    elif type in ['video/mp4', 'video/x-m4v']:
        type_info = 'MPEG-4 video (%s)' % type
    elif type in ['video/MP2T']:
        type_info = 'MPEG-2 transport stream (%s)' % type
    elif type in ['video/webm']:
        type_info = 'WebM video (%s)' % type
    # elif type in ['video/ogg']:
    #    type_info = 'Ogg video (%s)' % type
    elif type in ['video/quicktime']:
        type_info = 'QuickTime video (%s)' % type
    elif type in ['video/x-matroska']:
        type_info = 'Matroska video (%s)' % type
    # elif type in ['video/x-ms-wmv']:
    #    type_info = 'Windows Media video (%s)' % type
    elif type in ['video/x-ms-asf']:
        type_info = 'Advanced Systems Format (%s)' % type
    # elif type in ['video/mpeg']:
    #    type_info = 'MPEG video (%s)' % type
    elif type in ['audio/mp4', 'audio/m4a']:
        type_info = 'MPEG-4 audio (%s)' % type
    elif type in ['audio/mpeg']:
        type_info = 'MP3 (%s)' % type
    elif type in ['audio/wav', 'audio/wave', 'audio/x-wav']:
        type_info = 'Waveform Audio File Format ({})'.format(type)

    elif type in ['image/jpeg']:
        type_info = 'JPEG Image (%s)' % type
    elif type in ['image/png']:
        type_info = 'Portable Network Graphics (%s)' % type
    elif type in ['image/gif']:
        type_info = 'Graphics Interchange Format (%s)' % type
    elif type in ['m3u8']:
        if 'm3u8_type' in kwargs:
            if kwargs['m3u8_type'] == 'master':
                type_info = 'M3U8 Master {}'.format(type)
        else:
            type_info = 'M3U8 Playlist {}'.format(type)
    else:
        type_info = 'Unknown type (%s)' % type

    maybe_print('Site:      ', site_info)
    maybe_print('Title:     ', unescape_html(tr(title)))
    print('Type:      ', type_info)
    if type != 'm3u8':
        print(
            'Size:      ', round(size / (1 << 20), 2),
            'MiB (' + str(size) + ' Bytes)'
        )
    if type == 'm3u8' and 'm3u8_url' in kwargs:
        print('M3U8 Url:   {}'.format(kwargs['m3u8_url']))
    print()


def mime_to_container(mime: str) -> str:
    """
    Converts a MIME type to its corresponding container format extension.
    """
    mapping = {
        'video/3gpp': '3gp',
        'video/mp4': 'mp4',
        'video/webm': 'webm',
        'video/x-flv': 'flv',
    }
    return mapping.get(mime, mime.split('/')[1])


def parse_host(host: str) -> Tuple[str, int]:
    """
    Parses host name and port number from a string.

    Args:
        host (str): The host string to parse.

    Returns:
        Tuple[str, int]: A tuple containing the parsed hostname and port number.
    """
    # If the host is just a port number, assume it is bound to "0.0.0.0"
    if re.match(r'^(\d+)$', host) is not None:
        return ("0.0.0.0", int(host))
    # Ensure that the host string includes a scheme
    if re.match(r'^(\w+)://', host) is None:
        host = "//" + host
    # Parse the host string
    o = parse.urlparse(host)
    hostname = o.hostname or "0.0.0.0"
    port = o.port or 0
    return (hostname, port)


def set_proxy(proxy: Tuple[str, int]) -> None:
    proxy_url = f"{proxy[0]}:{proxy[1]}"
    proxy_handler = request.ProxyHandler({
        'http': proxy_url,
        'https': proxy_url,
    })
    # Build an opener and install it globally
    opener = request.build_opener(proxy_handler)
    request.install_opener(opener)


def unset_proxy() -> None:
    """
    Unsets the proxy settings globally.
    """
    proxy_handler = request.ProxyHandler({})
    opener = request.build_opener(proxy_handler)
    request.install_opener(opener)


# DEPRECATED in favor of set_proxy() and unset_proxy()
def set_http_proxy(proxy: Optional[str]) -> None:
    warnings.warn(
        "set_http_proxy() is deprecated, use set_proxy() and unset_proxy() instead",
        DeprecationWarning
    )
    if proxy is None:  # Use system default setting
        proxy_support = request.ProxyHandler()
    elif proxy == '':  # Don't use any proxy
        proxy_support = request.ProxyHandler({})
    else:  # Use proxy
        proxy_support = request.ProxyHandler(
            {'http': '%s' % proxy, 'https': '%s' % proxy}
        )
    opener = request.build_opener(proxy_support)
    request.install_opener(opener)


def print_more_compatible(*args: Any, **kwargs: Any) -> None:
    import builtins as __builtin__
    """Overload default print function as py (<3.3) does not support 'flush' keyword.
    Although the function name can be same as print to get itself overloaded automatically,
    I'd rather leave it with a different name and only overload it when importing to make less confusion.
    """
    # nothing happens on py3.3 and later
    if sys.version_info[:2] >= (3, 3):
        return __builtin__.print(*args, **kwargs)

    # in lower pyver (e.g. 3.2.x), remove 'flush' keyword and flush it as requested
    do_flush = kwargs.pop('flush', False)
    ret = __builtin__.print(*args, **kwargs)
    if do_flush:
        kwargs.get('file', sys.stdout).flush()
    return ret


def parse_url(
    url: str,
) -> Tuple[str, str]:
    """
    Parses a URL into its host and path components.

    This function uses regular expressions to extract the host and path components from a given URL.
    It supports both HTTP and HTTPS URLs.

    Args:
        url (str): The URL to parse.

    Returns:
        Tuple[str, str]: A tuple containing the host and path components of the URL.
    """
    return r1(r'https?://([^/]+)/', url), r1(r'https?://[^/]+(.*)', url)


def download_main(download, download_playlist, urls, playlist, **kwargs):
    for url in urls:
        if not re.match(r'https?://', url):
            url = 'http://' + url

        if m3u8:
            if output_filename:
                title = output_filename
            else:
                title = "m3u8file"
            download_url_ffmpeg(url=url, title=title,ext = 'mp4',output_dir = '.')
        elif playlist:
            download_playlist(url, **kwargs)
        else:
            download(url, **kwargs)


def load_cookies(cookiefile: str) -> None:
    """
    Loads cookies from a given file and stores them in the global `cookies` variable.

    The function supports two formats:
    - Plain text `.txt` files (typically in Netscape cookie format).
    - SQLite `.sqlite` files (typically in Chromium cookie format).

    Args:
        cookiefile (str): The path to the cookie file.

    Returns:
        None

    Raises:
        ValueError: If the cookiefile is not a valid cookie file.

    """
    global cookies
    if cookiefile.endswith('.txt'):
        # MozillaCookieJar treats prefix '#HttpOnly_' as comments incorrectly!
        # do not use its load()
        # see also:
        #   - https://docs.python.org/3/library/http.cookiejar.html#http.cookiejar.MozillaCookieJar
        #   - https://github.com/python/cpython/blob/4b219ce/Lib/http/cookiejar.py#L2014
        #   - https://curl.haxx.se/libcurl/c/CURLOPT_COOKIELIST.html#EXAMPLE
        #cookies = cookiejar.MozillaCookieJar(cookiefile)
        #cookies.load()
        cookies = MozillaCookieJar()
        now = time.time()
        ignore_discard, ignore_expires = False, False
        with open(cookiefile, 'r', encoding='utf-8') as f:
            for line in f:
                # last field may be absent, so keep any trailing tab
                if line.endswith("\n"):
                    line = line[:-1]

                # skip comments and blank lines XXX what is $ for?
                if (line.strip().startswith(("#", "$")) or
                    line.strip() == ""):
                    if not line.strip().startswith('#HttpOnly_'):  # skip for #HttpOnly_
                        continue

                domain, domain_specified, path, secure, expires, name, value = \
                        line.split("\t")
                secure = (secure == "TRUE")
                domain_specified = (domain_specified == "TRUE")
                if name == "":
                    # cookies.txt regards 'Set-Cookie: foo' as a cookie
                    # with no name, whereas http.cookiejar regards it as a
                    # cookie with no value.
                    name = value
                    value = None

                initial_dot = domain.startswith(".")
                if not line.strip().startswith('#HttpOnly_'):  # skip for #HttpOnly_
                    assert domain_specified == initial_dot

                discard = False
                if expires == "":
                    expires = None
                    discard = True

                # assume path_specified is false
                c = Cookie(0, name, value,
                           None, False,
                           domain, domain_specified, initial_dot,
                           path, False,
                           secure,
                           expires,
                           discard,
                           None,
                           None,
                           {})
                if not ignore_discard and c.discard:
                    continue
                if not ignore_expires and c.is_expired(now):
                    continue
                cookies.set_cookie(c)

    elif cookiefile.endswith(('.sqlite', '.sqlite3')):
        temp_dir = tempfile.gettempdir()
        temp_cookiefile = os.path.join(temp_dir, 'temp_cookiefile.sqlite')
        shutil.copy2(cookiefile, temp_cookiefile)

        cookies = MozillaCookieJar()
        con = sqlite3.connect(temp_cookiefile)
        cur = con.cursor()
        cur.execute("""SELECT host, path, isSecure, expiry, name, value
        FROM moz_cookies""")
        for item in cur.fetchall():
            c = Cookie(
                0, item[4], item[5], None, False, item[0],
                item[0].startswith('.'), item[0].startswith('.'),
                item[1], False, item[2], item[3], item[3] == '', None,
                None, {},
            )
            cookies.set_cookie(c)

    else:
        log.e('[error] unsupported cookies format')
        # TODO: Chromium Cookies
        # SELECT host_key, path, secure, expires_utc, name, encrypted_value
        # FROM cookies
        # http://n8henrie.com/2013/11/use-chromes-cookies-for-easier-downloading-with-python-requests/


def set_socks_proxy(proxy: str) -> None:
    """
    Sets up a SOCKS proxy for socket connections.

    This function sets up a SOCKS proxy for socket connections using the specified proxy string.
    It supports both SOCKS5 and SOCKS4A protocols.

    Args:
        proxy (str): The proxy string in the format "HOST:PORT" or "USERNAME:PASSWORD@HOST:PORT".

    Raises:
        ImportError: If the PySocks library is not installed.
        ValueError: If the proxy string is not in the correct format.
    """
    try:
        import socks
        if '@' in proxy:
            proxy_info = proxy.split("@")
            socks_proxy_addrs = proxy_info[1].split(':')
            socks_proxy_auth = proxy_info[0].split(":")
            socks.set_default_proxy(
                socks.SOCKS5,
                socks_proxy_addrs[0],
                int(socks_proxy_addrs[1]),
                True,
                socks_proxy_auth[0],
                socks_proxy_auth[1]
            )
        else:
            try:
                socks_proxy_addrs = proxy.split(':')
                assert len(socks_proxy_addrs) == 2 and socks_proxy_addrs[1].isdigit()
            except AssertionError:
                raise ValueError("Invalid SOCKS proxy format. Expected HOST:PORT.")
            socks.set_default_proxy(
               socks.SOCKS5,
               socks_proxy_addrs[0],
               int(socks_proxy_addrs[1]),
            )
        socket.socket = socks.socksocket

        def getaddrinfo(*args):
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))
            ]
        socket.getaddrinfo = getaddrinfo
    except ImportError:
        log.w(
            'Error importing PySocks library, socks proxy ignored.'
            'In order to use use socks proxy, please install PySocks.'
        )


def script_main(
    download: Callable, download_playlist: Callable, **kwargs: Any
) -> None:
    """
    Main script function for the application.

    This function is the entry point for the application and handles the command-line interface.
    It parses the command-line arguments, sets up logging, and calls the main download function.

    Args:
        download (Callable): The function to call for downloading a single URL.
        download_playlist (Callable): The function to call for downloading a playlist of URLs.
        **kwargs: Additional keyword arguments.
    """
    logging.basicConfig(format='[%(levelname)s] %(message)s')

    def print_version():
        version = get_version(
            kwargs['repo_path'] if 'repo_path' in kwargs else __version__
        )
        log.i(
            'version {}, a tiny downloader that scrapes the web.'.format(
                version
            )
        )

    parser = argparse.ArgumentParser(
        prog='you-get',
        usage='you-get [OPTION]... URL...',
        description='A tiny downloader that scrapes the web',
        add_help=False,
    )
    parser.add_argument(
        '-V', '--version', action='store_true',
        help='Print version and exit'
    )
    parser.add_argument(
        '-h', '--help', action='store_true',
        help='Print this help message and exit'
    )

    dry_run_grp = parser.add_argument_group(
        'Dry-run options', '(no actual downloading)'
    )
    dry_run_grp = dry_run_grp.add_mutually_exclusive_group()
    dry_run_grp.add_argument(
        '-i', '--info', action='store_true', help='Print extracted information'
    )
    dry_run_grp.add_argument(
        '-u', '--url', action='store_true',
        help='Print extracted information with URLs'
    )
    dry_run_grp.add_argument(
        '--json', action='store_true',
        help='Print extracted URLs in JSON format'
    )

    download_grp = parser.add_argument_group('Download options')
    download_grp.add_argument(
        '-n', '--no-merge', action='store_true', default=False,
        help='Do not merge video parts'
    )
    download_grp.add_argument(
        '--no-caption', action='store_true',
        help='Do not download captions (subtitles, lyrics, danmaku, ...)'
    )
    download_grp.add_argument(
        '--post', '--postfix', dest='postfix', action='store_true', default=False,
        help='Postfix downloaded files with unique identifiers'
    )
    download_grp.add_argument(
        '--pre', '--prefix', dest='prefix', metavar='PREFIX', default=None,
        help='Prefix downloaded files with string'
    )
    download_grp.add_argument(
        '-f', '--force', action='store_true', default=False,
        help='Force overwriting existing files'
    )
    download_grp.add_argument(
        '--skip-existing-file-size-check', action='store_true', default=False,
        help='Skip existing file without checking file size'
    )
    download_grp.add_argument(
        '-F', '--format', metavar='STREAM_ID',
        help='Set video format to STREAM_ID'
    )
    download_grp.add_argument(
        '-O', '--output-filename', metavar='FILE', help='Set output filename'
    )
    download_grp.add_argument(
        '-o', '--output-dir', metavar='DIR', default='.',
        help='Set output directory'
    )
    download_grp.add_argument(
        '-p', '--player', metavar='PLAYER',
        help='Stream extracted URL to a PLAYER'
    )
    download_grp.add_argument(
        '-c', '--cookies', metavar='COOKIES_FILE',
        help='Load cookies.txt or cookies.sqlite'
    )
    download_grp.add_argument(
        '-t', '--timeout', metavar='SECONDS', type=int, default=600,
        help='Set socket timeout'
    )
    download_grp.add_argument(
        '-d', '--debug', action='store_true',
        help='Show traceback and other debug info'
    )
    download_grp.add_argument(
        '-I', '--input-file', metavar='FILE', type=argparse.FileType('r'),
        help='Read non-playlist URLs from FILE'
    )
    download_grp.add_argument(
        '-P', '--password', help='Set video visit password to PASSWORD'
    )
    download_grp.add_argument(
        '-l', '--playlist', action='store_true',
        help='Prefer to download a playlist'
    )

    playlist_grp = parser.add_argument_group('Playlist optional options')
    playlist_grp.add_argument(
        '--first', metavar='FIRST',
        help='the first number'
    )
    playlist_grp.add_argument(
        '--last', metavar='LAST',
        help='the last number'
    )
    playlist_grp.add_argument(
        '--size', '--page-size', metavar='PAGE_SIZE',
        help='the page size number'
    )

    download_grp.add_argument(
        '-a', '--auto-rename', action='store_true', default=False,
        help='Auto rename same name different files'
    )

    download_grp.add_argument(
        '-k', '--insecure', action='store_true', default=False,
        help='ignore ssl errors'
    )

    proxy_grp = parser.add_argument_group('Proxy options')
    proxy_grp = proxy_grp.add_mutually_exclusive_group()
    proxy_grp.add_argument(
        '-x', '--http-proxy', metavar='HOST:PORT',
        help='Use an HTTP proxy for downloading'
    )
    proxy_grp.add_argument(
        '-y', '--extractor-proxy', metavar='HOST:PORT',
        help='Use an HTTP proxy for extracting only'
    )
    proxy_grp.add_argument(
        '--no-proxy', action='store_true', help='Never use a proxy'
    )
    proxy_grp.add_argument(
        '-s', '--socks-proxy', metavar='HOST:PORT or USERNAME:PASSWORD@HOST:PORT',
        help='Use an SOCKS5 proxy for downloading'
    )

    download_grp.add_argument('--stream', help=argparse.SUPPRESS)
    download_grp.add_argument('--itag', help=argparse.SUPPRESS)

    download_grp.add_argument('-m', '--m3u8', action='store_true', default=False,
        help = 'download video using an m3u8 url')

    download_grp.add_argument('--enhanced-progress', action='store_true', default=False,
        help='Use enhanced progress bar with ETA, speed trends (↑↓→), peak speeds, stall detection, and detailed bandwidth statistics')


    parser.add_argument('URL', nargs='*', help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.help:
        print_version()
        parser.print_help()
        sys.exit()
    if args.version:
        print_version()
        sys.exit()

    if args.debug:
        # Set level of root logger to DEBUG
        logging.getLogger().setLevel(logging.DEBUG)

    global force
    global skip_existing_file_size_check
    global dry_run
    global json_output
    global player
    global extractor_proxy
    global output_filename
    global auto_rename
    global insecure
    global m3u8
    global postfix
    global prefix
    global enhanced_progress
    output_filename = args.output_filename
    extractor_proxy = args.extractor_proxy

    info_only = args.info
    if args.force:
        force = True
    if args.skip_existing_file_size_check:
        skip_existing_file_size_check = True
    if args.auto_rename:
        auto_rename = True
    if args.url:
        dry_run = True
    if args.json:
        json_output = True
        # to fix extractors not use VideoExtractor
        dry_run = True
        info_only = False

    if args.cookies:
        load_cookies(args.cookies)

    if args.m3u8:
        m3u8 = True

    if args.enhanced_progress:
        enhanced_progress = True

    caption = True
    stream_id = args.format or args.stream or args.itag
    if args.no_caption:
        caption = False
    if args.player:
        player = args.player
        caption = False

    if args.insecure:
        # ignore ssl
        insecure = True

    postfix = args.postfix
    prefix = args.prefix

    if args.no_proxy:
        set_http_proxy('')
    else:
        set_http_proxy(args.http_proxy)
    if args.socks_proxy:
        set_socks_proxy(args.socks_proxy)

    urls = []
    if args.input_file:
        logging.debug('you are trying to load urls from %s', args.input_file)
        if args.playlist:
            log.e(
                "reading playlist from a file is unsupported "
                "and won't make your life easier"
            )
            sys.exit(2)
        urls.extend(line.strip() for line in args.input_file)
        args.input_file.close()
    urls.extend(args.URL)

    if not urls:
        parser.print_help()
        sys.exit()

    socket.setdefaulttimeout(args.timeout)

    try:
        extra = {'args': args}
        if extractor_proxy:
            extra['extractor_proxy'] = extractor_proxy
        if stream_id:
            extra['stream_id'] = stream_id
        download_main(
            download, download_playlist,
            urls, args.playlist,
            output_dir=args.output_dir, merge=not args.no_merge,
            info_only=info_only, json_output=json_output, caption=caption,
            password=args.password,
            **extra
        )
    except KeyboardInterrupt:
        if args.debug:
            raise
        else:
            sys.exit(1)
    except UnicodeEncodeError:
        if args.debug:
            raise
        log.e(
            '[error] oops, the current environment does not seem to support '
            'Unicode.'
        )
        log.e('please set it to a UTF-8-aware locale first,')
        log.e(
            'so as to save the video (with some Unicode characters) correctly.'
        )
        log.e('you can do it like this:')
        log.e('    (Windows)    % chcp 65001 ')
        log.e('    (Linux)      $ LC_CTYPE=en_US.UTF-8')
        sys.exit(1)
    except Exception:
        if not args.debug:
            log.e('[error] oops, something went wrong.')
            log.e(
                'don\'t panic, c\'est la vie. please try the following steps:'
            )
            log.e('  (1) Rule out any network problem.')
            log.e('  (2) Make sure you-get is up-to-date.')
            log.e('  (3) Check if the issue is already known, on')
            log.e('        https://github.com/soimort/you-get/wiki/Known-Bugs')
            log.e('        https://github.com/soimort/you-get/issues')
            log.e('  (4) Run the command with \'--debug\' option,')
            log.e('      and report this issue with the full output.')
        else:
            print_version()
            log.i(args)
            raise
        sys.exit(1)


def google_search(
    url: str
) -> str:
    """
    Search for a video on Google and return the first result.

    This function searches for a video on Google using the specified URL as a keyword,
    and returns the first result.

    Args:
        url (str): The URL to use as a keyword for the search.

    Returns:
        str: The URL of the first result from the Google search.
    """
    keywords = r1(r'https?://(.*)', url)
    url = 'https://www.google.com/search?tbm=vid&q=%s' % parse.quote(keywords)
    page = get_content(url, headers=fake_headers)
    videos = re.findall(
        r'(https://www\.youtube\.com/watch\?v=[\w-]+)', page
    )
    print('Best matched result:')
    return(videos[0])


def url_to_module(
    url: str
) -> Tuple[ModuleType, str]:
    """
    Converts a URL to a module and returns it along with the URL.

    This function takes a URL as input and attempts to convert it to a module.
    If the URL is not supported, it attempts to search for a video on Google and
    returns the first result.

    Args:
        url (str): The URL to convert to a module.

    Returns:
        Tuple[ModuleType, str]: A tuple containing the module and the URL.
    """
    try:
        video_host, video_url = parse_url(url)
    except AssertionError:
        log.warning("Google search is not available")
        url = google_search(url)
        video_host, video_url = parse_url(url)

    if video_host.endswith('.com.cn') or video_host.endswith('.ac.cn'):
        video_host = video_host[:-3]
    domain = r1(r'(\.[^.]+\.[^.]+)$', video_host) or video_host
    assert domain, 'unsupported url: ' + url

    # all non-ASCII code points must be quoted (percent-encoded UTF-8)
    url = ''.join([ch if ord(ch) in range(128) else parse.quote(ch) for ch in url])

    k = r1(r'([^.]+)', domain)
    if k in SITES:
        return (
            import_module('.'.join(['you_get', 'extractors', SITES[k]])),
            url
        )
    else:
        try:
            try:
                location = get_location(url) # t.co isn't happy with fake_headers
            except:
                location = get_location(url, headers=fake_headers)
        except:
            location = get_location(url, headers=fake_headers, get_method='GET')

        if location and location != url and not location.startswith('/'):
            return url_to_module(location)
        else:
            return import_module('you_get.extractors.universal'), url


def any_download(url: str, **kwargs: Any) -> None:
    """
    Download content from the specified URL using an appropriate module.

    This function determines which module to use for downloading based on the URL,
    then calls the `download` method from the chosen module with any keyword arguments.

    Args:
        url (str): The URL from which the content will be downloaded.
        **kwargs (Any): Additional keyword arguments passed to the `download` method
                        of the chosen module based on the URL.
    """
    m, url = url_to_module(url)
    m.download(url, **kwargs)


def any_download_playlist(url, **kwargs):
    m, url = url_to_module(url)
    m.download_playlist(url, **kwargs)


def main(**kwargs):
    script_main(any_download, any_download_playlist, **kwargs)
