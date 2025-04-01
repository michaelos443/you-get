#!/usr/bin/env python

from .common import (
    match1, maybe_print, download_urls, get_filename, parse_host, set_proxy,
    unset_proxy, get_content, dry_run, player, print_more_compatible as print_compat,
)
from .util import log
from typing import Union, Any, Optional, List, Dict
from . import json_output
from urllib.parse import urlparse, urlunparse, ParseResult
import os
from pathlib import Path
import sys

VALID_SCHEMES = ['http', 'https']


def validate_url(url: str) -> str:
    """
    Validates and normalizes a given URL.

    This function ensures that the URL has a valid scheme (either 'http' or 'https').
    If the URL does not include a scheme, it defaults to 'http'. Additionally, the function
    checks that the URL has a valid netloc (i.e., domain or host).
    If the netloc is missing, a ValueError is raised.

    Args:
        url (str): The URL to validate and normalize.

    Returns:
        str: The normalized URL.

    Raises:
        ValueError: If the URL does not include a valid scheme or netloc.
    """
    parsed_url =  urlparse(url)
    if not parsed_url.scheme or parsed_url.scheme not in VALID_SCHEMES:
        parsed_url = parsed_url._replace(scheme="http")
    if not parsed_url.netloc:
        raise ValueError(
            f"Invalid URL: {url} Missing netloc."
            f" Ensure the URL is valid and includes a scheme and netloc."
        )
    return urlunparse(parsed_url)


class Extractor():
    def __init__(
        self, *args: Any
    ) -> None:
        self.url = None
        self.title = None
        self.vid = None
        self.streams = {}
        self.streams_sorted = []

        self.url = args[0] if args else None


class VideoExtractor():
    def __init__(self, *args: Any) -> None:
        self.url = None
        self.title = None
        self.vid = None
        self.m3u8_url = None
        self.streams = {}
        self.streams_sorted = []
        self.audiolang = None
        self.password_protected = False
        self.dash_streams: Dict[str, Any] = {}
        self.caption_tracks = {}
        self.out = False
        self.ua = None
        self.referer = None
        self.danmaku = None
        self.lyrics = None

        if args:
            self.url = args[0]

    def download_by_url(self, url: str, **kwargs: Any) -> None:
        """
        Downloads video content based on the provided URL.
        Optionally accepts additional keyword arguments for proxy configuration and extraction.

        Args:
            url (str): The URL to download.
            **kwargs: Additional keyword arguments for proxy configuration and extraction.
        """
        url = validate_url(url)
        self.url = url
        self.vid = None

        extractor_proxy = kwargs.get('extractor_proxy')

        if extractor_proxy:
            set_proxy(parse_host(extractor_proxy))

        self.prepare(**kwargs)
        if self.out:
            return

        if extractor_proxy:
            unset_proxy()

        try:
            self.streams_sorted = [
                {'id': stream_type['id'], **self.streams[stream_type['id']]}
                for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams
            ]
        except KeyError as e:
            log.e(f"Stream type missing key: {e}")
            self.streams_sorted = [
                dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items()))
                for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams
            ]

        self.extract(**kwargs)

        self.download(**kwargs)

    def manage_proxy(self, proxy: Optional[str], action: str) -> None:
        """
        Manages proxy settings for the extractor.

        This function allows setting or unsetting a proxy for the current download session.
        When setting a proxy, it validates the proxy string before applying it.

        Args:
            proxy (Optional[str]): The proxy URL to use. Required when action is "set".
            action (str): The action to perform. Must be either "set" or "unset".

        Raises:
            ValueError: If the action is not "set" or "unset", or if proxy is None when action is "set".
        """
        if action not in ["set", "unset"]:
            raise ValueError(f"Invalid action: {action}. Must be either 'set' or 'unset'.")

        if action == "set":
            if proxy is None:
                raise ValueError("Proxy URL cannot be None when setting a proxy.")
            set_proxy(parse_host(proxy))
        else:  # action == "unset"
            unset_proxy()

    def download_by_vid(
        self, vid: str, **kwargs: Any
    ) -> None:
        """
        Downloads video content based on the provided video ID (vid).
        Optionally accepts additional keyword arguments for proxy configuration and extraction.

        Args:
            vid (str): The video ID to download.
            **kwargs: Additional keyword arguments for proxy configuration and extraction.
        """
        self.url = None  # Placeholder for video URL.
        self.vid = vid  # Set the video ID.

        # Check if a proxy is specified and set it up.
        use_proxy = kwargs.get('extractor_proxy')
        if use_proxy:
            set_proxy(parse_host(use_proxy))

        self.prepare(**kwargs)
        if use_proxy:
            unset_proxy()

        valid_stream_ids = {stream_type['id']: stream_type for stream_type in self.__class__.stream_types}
        self.streams_sorted = [
            {**{'id': stream_id}, **self.streams[stream_id]}
            for stream_id in valid_stream_ids if stream_id in self.streams
        ]

        self.extract(**kwargs)

        self.download(**kwargs)

    def prepare(
        self, **kwargs: Any
    ) -> None:
        raise NotImplementedError("This method must be implemented by subclasses.")

    def extract(
        self, **kwargs: Any
    ) -> None:
        pass
        # raise NotImplementedError()

    def p_stream(self, stream_id: Union[str, int]) -> None:
        stream = self.streams.get(stream_id) or self.dash_streams.get(stream_id)

        if 'itag' in stream:
            print("    - itag:          %s" % log.sprint(stream_id, log.NEGATIVE))
        else:
            print("    - format:        %s" % log.sprint(stream_id, log.NEGATIVE))

        if 'container' in stream:
            print("      container:     %s" % stream['container'])

        if 'video_profile' in stream:
            maybe_print("      video-profile: %s" % stream['video_profile'])

        if 'quality' in stream:
            print("      quality:       %s" % stream['quality'])

        if 'size' in stream and 'container' in stream and stream['container'].lower() != 'm3u8':
            if stream['size'] != float('inf')  and stream['size'] != 0:
                print("      size:          %s MiB (%s bytes)" % (round(stream['size'] / (1 << 20), 1), stream['size']))

        if 'm3u8_url' in stream:
            print("      m3u8_url:      {}".format(stream['m3u8_url']))

        if 'itag' in stream:
            print("    # download-with: %s" % log.sprint("you-get --itag=%s [URL]" % stream_id, log.UNDERLINE))
        else:
            print("    # download-with: %s" % log.sprint("you-get --format=%s [URL]" % stream_id, log.UNDERLINE))

        print_compat()

    def p_i(
        self, stream_id: Union[str, int]
    ) -> None:
        """
        Prints detailed information about the specific video stream, including its title, size, and URL.

        Args:
            stream_id (Union[str, int]): The ID of the video stream to print information about.

        """
        if stream_id in self.streams:
            stream = self.streams[stream_id]
        else:
            stream = self.dash_streams[stream_id]

        maybe_print("    - title:         %s" % self.title)
        print("       size:         %s MiB (%s bytes)" % (round(stream['size'] / (1 << 20), 1), stream['size']))
        print("        url:         %s" % self.url)
        print_compat()

        sys.stdout.flush()

    def print_stream_info(self,
                          stream_id: Optional[Union[str, int, List[str]]] = None) -> None:
        maybe_print("site:                %s" % self.__class__.name)
        maybe_print("title:               %s" % self.title)
        if stream_id:
            # Print the stream
            print("stream:")
            self.p_stream(stream_id)

        elif stream_id is None:
            # Print stream with best quality
            print("stream:              # Best quality")
            stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
            self.p_stream(stream_id)

        elif stream_id == []:
            print("streams:             # Available quality and codecs")
            # Print DASH streams
            if self.dash_streams:
                print("    [ DASH ] %s" % ('_' * 36))
                itags = sorted(self.dash_streams,
                               key=lambda i: self.dash_streams[i]['size'],
                               reverse=True)
                for stream in itags[:10]:
                    self.p_stream(stream)
            # Print all other available streams
            if self.streams_sorted:
                print("    [ DEFAULT ] %s" % ('_' * 33))
                for stream in self.streams_sorted:
                    self.p_stream(stream['id'] if 'id' in stream else stream['itag'])

        if self.audiolang:
            print("audio-languages:")
            for i in self.audiolang:
                print("    - lang:          {}".format(i['lang']))
                print("      download-url:  {}\n".format(i['url']))

        sys.stdout.flush()

    def p_playlist(self, stream_id: Union[str, int, None] = None) -> None:
        maybe_print(f"site:                {self.__class__.name}")
        print(f"playlist:            {self.title}")
        print("videos:")

    def download(self, **kwargs: Any) -> None:
        if kwargs.get('json_output', False):
            json_output.output(self)
        elif 'info_only' in kwargs and kwargs['info_only']:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Display the stream
                stream_id = kwargs['stream_id']
                if 'index' not in kwargs:
                    self.print_stream_info(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                # Display all available streams
                if 'index' not in kwargs:
                    self.print_stream_info([])
                else:
                    stream_id = (
                        self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0]
                        else self.streams_sorted[0]['itag']
                    )
                    self.p_i(stream_id)

        else:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Download the stream
                stream_id = kwargs['stream_id']
            else:
                # Download stream with the best quality
                from .processor.ffmpeg import has_ffmpeg_installed
                if has_ffmpeg_installed() and player is None and self.dash_streams or not self.streams_sorted:
                    #stream_id = list(self.dash_streams)[-1]
                    itags = sorted(self.dash_streams,
                                   key=lambda i: -self.dash_streams[i]['size'])
                    stream_id = itags[0]
                else:
                    stream_id = (
                        self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0]
                        else self.streams_sorted[0]['itag']
                    )

            if 'index' not in kwargs:
                self.print_stream_info(stream_id)
            else:
                self.p_i(stream_id)

            if stream_id in self.streams:
                urls = self.streams[stream_id]['src']
                ext = self.streams[stream_id]['container']
                total_size = self.streams[stream_id]['size']
            else:
                urls = self.dash_streams[stream_id]['src']
                ext = self.dash_streams[stream_id]['container']
                total_size = self.dash_streams[stream_id]['size']

            if ext == 'm3u8' or ext == 'm4a':
                ext = 'mp4'

            if not urls:
                log.e('[Error] Video source extraction failed. URL: {}'.format(self.url))
            # For legacy main()
            headers = {}
            if self.ua is not None:
                headers['User-Agent'] = self.ua
            if self.referer is not None:
                headers['Referer'] = self.referer
            download_urls(urls, self.title, ext, total_size, headers=headers,
                          output_dir=kwargs['output_dir'],
                          merge=kwargs['merge'],
                          av=stream_id in self.dash_streams,
                          vid=self.vid)

            if 'caption' not in kwargs or not kwargs['caption']:
                print('Skipping captions or danmaku.')
                return

            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print('Saving %s ... ' % filename, end="", flush=True)
                srt = self.caption_tracks[lang]
                with open(os.path.join(kwargs['output_dir'], filename),
                          'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')

            if self.danmaku is not None and not dry_run:
                filename = '{}.cmt.xml'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                filepath = Path(kwargs['output_dir']).resolve() / filename
                with open(filepath, 'x', encoding='utf8') as fp:
                    fp.write(self.danmaku)

            if self.lyrics is not None and not dry_run:
                filename = '{}.lrc'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                filepath = Path(kwargs['output_dir']) / filename
                with open(filepath, 'w', encoding='utf8') as fp:
                    fp.write(self.lyrics)

            # Handles downloads for main_dev() mode, ensuring compatibility with FFmpeg if installed.
            #download_urls(urls, self.title, self.streams[stream_id]['container'], self.streams[stream_id]['size'])
        keep_obj = kwargs.get('keep_obj', False)
        if not keep_obj:
            self.__init__()
