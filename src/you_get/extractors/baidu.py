#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ['baidu_download']

from ..common import *
from .embed import *
from .universal import *
from typing import Iterable, Dict, Any, Tuple, Optional, List
import getpass
from functools import lru_cache


BASE_URL = "http://music.baidu.com"
LYRIC_BASE_URL = f"{BASE_URL}/data/music/fmlink?songIds="


@lru_cache(maxsize=128)
def baidu_get_song_data(
    sid: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch song data from Baidu Music API by song ID.

    Args:
        sid (str): Song ID.

    Returns:
        Optional[Dict[str, Any]]: Song data or None if song not found.
    """
    url = f'{LYRIC_BASE_URL}{sid}'
    try:
        data = json.loads(get_html(
            url, faker=True))['data']
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON response from {url} for song ID {sid}: {e}")
        return None

    return data['songList'][0] if data['xcode'] else None


def baidu_get_song_url(
    data: dict
) -> str:
    return data['songLink']


def baidu_get_song_artist(data: dict) -> str:
    return data['artistName']


def baidu_get_song_album(data: dict) -> str:
    return data['albumName']


def baidu_get_song_title(data: dict) -> str:
    return data['songName']


def baidu_get_song_info(data: dict, key: str) -> Optional[str]:
    return data.get(key)


def baidu_get_song_lyric(data: dict) -> Optional[str]:
    lrc = data['lrcLink']
    return f"http://music.baidu.com{lrc}" if lrc else None


def baidu_get_song_attribute(data: dict, attribute: str) -> Optional[str]:
    return data.get(attribute)


def baidu_download_song(
    sid, output_dir='.', merge=True, info_only=False):
    data = baidu_get_song_data(sid)
    if data is not None:
        url = baidu_get_song_info(data, 'songLink')
        title = baidu_get_song_title(data)
        artist = baidu_get_song_artist(data)
        album = baidu_get_song_album(data)
        lrc = baidu_get_song_lyric(data)
        file_name = f"{title} - {album} - {artist}"
    else:
        html = get_html("http://music.baidu.com/song/%s" % sid)
        url = r1(r'data_url="([^"]+)"', html)
        title = r1(r'data_name="([^"]+)"', html)
        file_name = title

    type, ext, size = url_info(url, faker=True)
    print_info(site_info, title, type, size)
    if not info_only:
        download_urls([url], file_name, ext, size,
                      output_dir, merge=merge, faker=True)

    try:
        type, ext, size = url_info(lrc, faker=True)
        print_info(site_info, title, type, size)
        if not info_only:
            download_urls([lrc], file_name, ext, size, output_dir, faker=True)
    except Exception as e:
        logging.error(f"Failed to get lyrics: {e}")


def baidu_download_album(
    aid: str, output_dir: str = '.', merge: bool = True, info_only: bool = False
) -> None:
    """
    Downloads an album from Baidu Music.

    Args:
        aid (str): The ID of the album to download.
        output_dir (str, optional): The directory to save the downloaded files. Defaults to '.'.
        merge (bool, optional): Whether to merge the downloaded files into a single file. Defaults to True.
        info_only (bool, optional): Whether to only print information about the downloaded files. Defaults to False.
    """
    html = get_html('http://music.baidu.com/album/%s' % aid, faker=True)
    album_name = r1(r'<h2 class="album-name">(.+?)<\/h2>', html) or "Unknown Album"
    artist = r1(r'<span class="author_list" title="(.+?)">', html)
    output_dir = f'{output_dir}/{artist} - {album_name}'
    ids = json.loads(r1(r'<span class="album-add" data-adddata=\'(.+?)\'>',
                        html).replace('&quot', '').replace(';', '"'))['ids']
    track_nr = 1
    for id in ids:
        song_data = baidu_get_song_data(id)
        song_url = baidu_get_song_url(song_data)
        song_title = baidu_get_song_title(song_data)
        song_lrc = baidu_get_song_lyric(song_data)
        file_name = '%02d.%s' % (track_nr, song_title)

        type, ext, size = url_info(song_url, faker=True)
        print_info(site_info, song_title, type, size)
        if not info_only:
            download_urls([song_url], file_name, ext, size,
                          output_dir, merge=merge, faker=True)

        if song_lrc:
            type, ext, size = url_info(song_lrc, faker=True)
            print_info(site_info, song_title, type, size)
            if not info_only:
                download_urls([song_lrc], file_name, ext,
                              size, output_dir, faker=True)

        track_nr += 1


def baidu_download(
    url: str, output_dir: str = '.', stream_type: Optional[str] = None, merge: bool = True, info_only: bool = False, **kwargs: Dict[str, Any]
) -> None:
    """
    Downloads a song, album, or image from Baidu Music or Baidu Tieba.

    Args:
        url (str): The URL of the song, album, or image to download.
        output_dir (str, optional): The directory to save the downloaded file. Defaults to '.'.
        stream_type (Optional[str], optional): The stream type to download. Defaults to None.
        merge (bool, optional): Whether to merge the downloaded files into a single file. Defaults to True.
        info_only (bool, optional): Whether to only print information about the downloaded file. Defaults to False.
        **kwargs: Additional keyword arguments.
    """

    if re.match(r'https?://pan.baidu.com', url):
        real_url, title, ext, size = baidu_pan_download(url)
        print_info('BaiduPan', title, ext, size)
        if not info_only:
            print('Hold on...')
            time.sleep(5)
            download_urls([real_url], title, ext, size,
                          output_dir, url, merge=merge, faker=True)
    elif re.match(r'https?://music.baidu.com/album/\d+', url):
        id = r1(r'https?://music.baidu.com/album/(\d+)', url)
        baidu_download_album(id, output_dir, merge, info_only)

    elif re.match(r'https?://music.baidu.com/song/\d+', url):
        id = r1(r'https?://music.baidu.com/song/(\d+)', url)
        baidu_download_song(id, output_dir, merge, info_only)

    elif re.match('https?://tieba.baidu.com/', url):
        try:
            # embedded videos
            embed_download(url, output_dir, merge=merge, info_only=info_only, **kwargs)
        except:
            # images
            html = get_html(url)
            title = r1(r'title:"([^"]+)"', html)

            vhsrc = re.findall(r'"BDE_Image"[^>]+src="([^"]+\.mp4)"', html) or \
                re.findall(r'vhsrc="([^"]+)"', html)
            if len(vhsrc) > 0:
                ext = 'mp4'
                size = url_size(vhsrc[0])
                print_info(site_info, title, ext, size)
                if not info_only:
                    download_urls(vhsrc, title, ext, size,
                                  output_dir=output_dir, merge=False)

            items = re.findall(
                r'//tiebapic.baidu.com/forum/w[^"]+/([^/"]+)', html)
            urls = ['http://tiebapic.baidu.com/forum/pic/item/' + i
                    for i in set(items)]

            # handle albums
            kw = r1(r'kw=([^&]+)', html) or r1(r"kw:'([^']+)'", html)
            tid = r1(r'tid=(\d+)', html) or r1(r"tid:'([^']+)'", html)
            album_url = f'http://tieba.baidu.com/photo/g/bw/picture/list?kw={kw}&tid={tid}&pe=1000'
            album_info = json.loads(get_content(album_url))
            for i in album_info['data']['pic_list']:
                urls.append(
                    'http://tiebapic.baidu.com/forum/pic/item/' + i['pic_id'] + '.jpg')

            ext = 'jpg'
            size = float('Inf')
            print_info(site_info, title, ext, size)

            if not info_only:
                download_urls(urls, title, ext, size,
                              output_dir=output_dir, merge=False)


def baidu_pan_download(url: str) -> tuple:
    """
    Handles the downloading of files from Baidu Pan.

    Args:
        url (str): The URL of the file to download.

    Returns:
        tuple: A tuple containing the real URL, title, extension, and size of the file.
    """
    errno_patt = r'errno":([^"]+),'
    refer_url = ""
    fake_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Host': 'pan.baidu.com',
        'Origin': 'http://pan.baidu.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:13.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2500.0 Safari/537.36',
        'Referer': refer_url
    }
    if cookies:
        print('Use user specified cookies')
    else:
        print('Generating cookies...')
        fake_headers['Cookie'] = baidu_pan_gen_cookies(url)
    refer_url = "http://pan.baidu.com"
    html = get_content(url, fake_headers, decoded=True)
    isprotected = False
    sign, timestamp, bdstoken, appid, primary_id, fs_id, uk = baidu_pan_parse(
        html)
    if sign == None:
        if re.findall(r'\baccess-code\b', html):
            isprotected = True
            sign, timestamp, bdstoken, appid, primary_id, fs_id, uk, fake_headers, psk = baidu_pan_protected_share(
                url)
            # raise NotImplementedError("Password required!")
        if isprotected != True:
            raise AssertionError("Share not found or canceled: %s" % url)
    if bdstoken == None:
        bdstoken = ""
    if isprotected != True:
        sign, timestamp, bdstoken, appid, primary_id, fs_id, uk = baidu_pan_parse(
            html)
    request_url = "http://pan.baidu.com/api/sharedownload?sign=%s&timestamp=%s&bdstoken=%s&channel=chunlei&clienttype=0&web=1&app_id=%s" % (
        sign, timestamp, bdstoken, appid)
    refer_url = url
    post_data = {
        'encrypt': 0,
        'product': 'share',
        'uk': uk,
        'primaryid': primary_id,
        'fid_list': '[' + fs_id + ']'
    }
    if isprotected == True:
        post_data['sekey'] = psk
    response_content = post_content(request_url, fake_headers, post_data, True)
    errno = match1(response_content, errno_patt)
    if errno != "0":
        raise AssertionError(
            "Server refused to provide download link! (Errno:%s)" % errno)
    real_url = r1(r'dlink":"([^"]+)"', response_content).replace('\\/', '/')
    title = r1(r'server_filename":"([^"]+)"', response_content)
    assert real_url
    type, ext, size = url_info(real_url, faker=True)
    title_wrapped = json.loads('{"wrapper":"%s"}' % title)
    title = title_wrapped['wrapper']
    logging.debug(real_url)
    return real_url, title, ext, size


def baidu_pan_parse(
    html: str
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    sign_patt = r'sign":"([^"]+)"'
    timestamp_patt = r'timestamp":([^"]+),'
    appid_patt = r'app_id":"([^"]+)"'
    bdstoken_patt = r'bdstoken":"([^"]+)"'
    fs_id_patt = r'fs_id":([^"]+),'
    uk_patt = r'uk":([^"]+),'
    errno_patt = r'errno":([^"]+),'
    primary_id_patt = r'shareid":([^"]+),'
    sign = match1(html, sign_patt)
    timestamp = match1(html, timestamp_patt)
    appid = match1(html, appid_patt)
    bdstoken = match1(html, bdstoken_patt)
    fs_id = match1(html, fs_id_patt)
    uk = match1(html, uk_patt)
    primary_id = match1(html, primary_id_patt)
    return sign, timestamp, bdstoken, appid, primary_id, fs_id, uk


def baidu_pan_gen_cookies(url: str, post_data: Optional[Dict[str, Any]] = None) -> str:
    from http import cookiejar
    cookiejar = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookiejar))
    resp = opener.open('http://pan.baidu.com')
    if post_data is not None:
        resp = opener.open(url, bytes(parse.urlencode(post_data), 'utf-8'))
    return cookjar2hdr(cookiejar)


def baidu_pan_protected_share(url: str) -> Tuple[str, str, str, str, str, str, str, Dict[str, Any], str]:
    print('This share is protected by password!')
    inpwd = getpass.getpass('Please provide unlock password: ').strip()
    inpwd = inpwd.replace(' ', '').replace('\t', '')
    print('Please wait...')
    post_pwd = {
        'pwd': inpwd,
        'vcode': None,
        'vstr': None
    }
    from http import cookiejar
    import time
    cookiejar = cookiejar.CookieJar()
    opener = request.build_opener(request.HTTPCookieProcessor(cookiejar))
    resp = opener.open('http://pan.baidu.com')
    resp = opener.open(url)
    init_url = resp.geturl()
    verify_url = 'http://pan.baidu.com/share/verify?%s&t=%s&channel=chunlei&clienttype=0&web=1' % (
        init_url.split('?', 1)[1], int(time.time()))
    refer_url = init_url
    fake_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'UTF-8,*;q=0.5',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Host': 'pan.baidu.com',
        'Origin': 'http://pan.baidu.com',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:13.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2500.0 Safari/537.36',
        'Referer': refer_url
    }
    opener.addheaders = dict2triplet(fake_headers)
    pwd_resp = opener.open(verify_url, bytes(
        parse.urlencode(post_pwd), 'utf-8'))
    pwd_resp_str = ungzip(pwd_resp.read()).decode('utf-8')
    pwd_res = json.loads(pwd_resp_str)
    if pwd_res['errno'] != 0:
        raise AssertionError(
            'Server returned an error: %s (Incorrect password?)' % pwd_res['errno'])
    pg_resp = opener.open('http://pan.baidu.com/share/link?%s' %
                          init_url.split('?', 1)[1])
    content = ungzip(pg_resp.read()).decode('utf-8')
    sign, timestamp, bdstoken, appid, primary_id, fs_id, uk = baidu_pan_parse(
        content)
    psk = query_cookiejar(cookiejar, 'BDCLND')
    psk = parse.unquote(psk)
    fake_headers['Cookie'] = cookjar2hdr(cookiejar)
    return sign, timestamp, bdstoken, appid, primary_id, fs_id, uk, fake_headers, psk


def cookjar2hdr(cookiejar: Iterable) -> str:
    cookie_str = ''
    for i in cookiejar:
        cookie_str = cookie_str + i.name + '=' + i.value + ';'
    return cookie_str[:-1]


def query_cookiejar(
    cookiejar: Iterable, name: str
) -> str:
    for i in cookiejar:
        if i.name == name:
            return i.value


def dict2triplet(dictin: Dict[str, Any]) -> List[Tuple[str, str]]:
    out_triplet = []
    for i in dictin:
        out_triplet.append((i, dictin[i]))
    return out_triplet

site_info = "Baidu.com"
download = baidu_download
download_playlist = playlist_not_supported("baidu")
