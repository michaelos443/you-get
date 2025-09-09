#!/usr/bin/env python

"""Extractor module for you-get.

This module provides base classes for extracting video information and downloading
videos from various websites. It defines the common interface and functionality
for all specific site extractors.
"""

from typing import Dict, List, Optional, Union, Any, Tuple
from .common import match1, maybe_print, download_urls, get_filename, parse_host, set_proxy, unset_proxy, get_content, dry_run, player
from .common import print_more_compatible as print
from .util import log
from . import json_output
import os
import sys

class Extractor():
    """Base class for all extractors.

    This class provides basic properties and methods for extracting video information.
    It is designed to be extended by specific site extractors.
    """

    def __init__(self, *args: str) -> None:
        """Initialize the extractor with optional URL.

        Args:
            *args: Variable length argument list, first argument is treated as URL if provided
        """
        self.url: Optional[str] = None
        self.title: Optional[str] = None
        self.vid: Optional[str] = None
        self.streams: Dict[str, Dict[str, Any]] = {}
        self.streams_sorted: List[Dict[str, Any]] = []

        if args:
            self.url = args[0]

class VideoExtractor():
    """Base class for video extractors.

    This class extends the basic Extractor with video-specific properties and methods.
    It provides functionality for downloading videos, handling streams, and displaying
    video information.
    """

    def __init__(self, *args: str) -> None:
        """Initialize the video extractor with optional URL.

        Args:
            *args: Variable length argument list, first argument is treated as URL if provided
        """
        self.url: Optional[str] = None
        self.title: Optional[str] = None
        self.vid: Optional[str] = None
        self.m3u8_url: Optional[str] = None
        self.streams: Dict[str, Dict[str, Any]] = {}
        self.streams_sorted: List[Dict[str, Any]] = []
        self.audiolang: Optional[List[Dict[str, str]]] = None
        self.password_protected: bool = False
        self.dash_streams: Dict[str, Dict[str, Any]] = {}
        self.caption_tracks: Dict[str, str] = {}
        self.out: bool = False
        self.ua: Optional[str] = None
        self.referer: Optional[str] = None
        self.danmaku: Optional[str] = None
        self.lyrics: Optional[str] = None

        if args:
            self.url = args[0]

    def download_by_url(self, url: str, **kwargs: Any) -> None:
        """Download video from URL.

        This method sets up the extractor with the given URL, prepares the download,
        extracts stream information, and initiates the download process.

        Args:
            url: The URL to download from
            **kwargs: Additional keyword arguments for the download process
        """
        self.url = url
        self.vid = None

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))
        self.prepare(**kwargs)
        if self.out:
            return
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            unset_proxy()

        try:
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
        except:
            self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]

        self.extract(**kwargs)

        self.download(**kwargs)

    def download_by_vid(self, vid: str, **kwargs: Any) -> None:
        """Download video by its ID.

        This method sets up the extractor with the given video ID, prepares the download,
        extracts stream information, and initiates the download process.

        Args:
            vid: The video ID to download
            **kwargs: Additional keyword arguments for the download process
        """
        self.url = None
        self.vid = vid

        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            set_proxy(parse_host(kwargs['extractor_proxy']))
        self.prepare(**kwargs)
        if 'extractor_proxy' in kwargs and kwargs['extractor_proxy']:
            unset_proxy()

        try:
            self.streams_sorted = [dict([('id', stream_type['id'])] + list(self.streams[stream_type['id']].items())) for stream_type in self.__class__.stream_types if stream_type['id'] in self.streams]
        except:
            self.streams_sorted = [dict([('itag', stream_type['itag'])] + list(self.streams[stream_type['itag']].items())) for stream_type in self.__class__.stream_types if stream_type['itag'] in self.streams]

        self.extract(**kwargs)

        self.download(**kwargs)

    def prepare(self, **kwargs: Any) -> None:
        """Prepare for extraction.

        This method should be implemented by subclasses to prepare for video extraction.
        It typically involves fetching video information, setting up necessary parameters,
        and preparing stream information.

        Args:
            **kwargs: Additional keyword arguments for preparation
        """
        pass
        #raise NotImplementedError()

    def extract(self, **kwargs: Any) -> None:
        """Extract video streams.

        This method should be implemented by subclasses to extract video streams.
        It typically involves parsing video source information and populating
        the streams dictionary.

        Args:
            **kwargs: Additional keyword arguments for extraction
        """
        pass
        #raise NotImplementedError()

    def p_stream(self, stream_id: str) -> None:
        """Print stream information.

        This method prints detailed information about a specific stream.

        Args:
            stream_id: The ID of the stream to print information for
        """
        if stream_id in self.streams:
            stream = self.streams[stream_id]
        else:
            stream = self.dash_streams[stream_id]

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
                print("      size:          %s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size']))

        if 'm3u8_url' in stream:
            print("      m3u8_url:      {}".format(stream['m3u8_url']))

        if 'itag' in stream:
            print("    # download-with: %s" % log.sprint("you-get --itag=%s [URL]" % stream_id, log.UNDERLINE))
        else:
            print("    # download-with: %s" % log.sprint("you-get --format=%s [URL]" % stream_id, log.UNDERLINE))

        print()

    def p_i(self, stream_id: str) -> None:
        """Print stream information in a compact format.

        This method prints basic information about a specific stream in a compact format.

        Args:
            stream_id: The ID of the stream to print information for
        """
        if stream_id in self.streams:
            stream = self.streams[stream_id]
        else:
            stream = self.dash_streams[stream_id]

        maybe_print("    - title:         %s" % self.title)
        print("       size:         %s MiB (%s bytes)" % (round(stream['size'] / 1048576, 1), stream['size']))
        print("        url:         %s" % self.url)
        print()

        sys.stdout.flush()

    def p(self, stream_id: Optional[Union[str, List]] = None) -> None:
        """Print video information.

        This method prints information about the video and its streams.

        Args:
            stream_id: The ID of the stream to print information for, or None for the best quality,
                      or an empty list to print all available streams
        """
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
                               key=lambda i: -self.dash_streams[i]['size'])
                for stream in itags:
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

    def p_playlist(self, stream_id: Optional[str] = None) -> None:
        """Print playlist information.

        This method prints information about a video playlist.

        Args:
            stream_id: The ID of the stream to print information for
        """
        maybe_print("site:                %s" % self.__class__.name)
        print("playlist:            %s" % self.title)
        print("videos:")

    def download(self, **kwargs: Any) -> None:
        """Download the video.

        This method handles the actual downloading of the video based on the extracted
        stream information. It supports various options like info-only mode, stream selection,
        and caption downloading.

        Args:
            **kwargs: Additional keyword arguments for the download process, including:
                      - json_output: Whether to output in JSON format
                      - info_only: Whether to only display information without downloading
                      - stream_id: The ID of the stream to download
                      - index: Whether to use the compact display format
                      - output_dir: Directory to save the downloaded files
                      - merge: Whether to merge video parts
                      - caption: Whether to download captions
                      - keep_obj: Whether to keep the extractor object after download
        """
        if 'json_output' in kwargs and kwargs['json_output']:
            json_output.output(self)
        elif 'info_only' in kwargs and kwargs['info_only']:
            if 'stream_id' in kwargs and kwargs['stream_id']:
                # Display the stream
                stream_id = kwargs['stream_id']
                if 'index' not in kwargs:
                    self.p(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                # Display all available streams
                if 'index' not in kwargs:
                    self.p([])
                else:
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']
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
                    stream_id = self.streams_sorted[0]['id'] if 'id' in self.streams_sorted[0] else self.streams_sorted[0]['itag']

            if 'index' not in kwargs:
                self.p(stream_id)
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
                log.wtf('[Failed] Cannot extract video source.')
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
                          vid=self.vid,
                          source_url=self.url,
                          **kwargs)

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
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.danmaku)

            if self.lyrics is not None and not dry_run:
                filename = '{}.lrc'.format(get_filename(self.title))
                print('Downloading {} ...\n'.format(filename))
                with open(os.path.join(kwargs['output_dir'], filename), 'w', encoding='utf8') as fp:
                    fp.write(self.lyrics)

            # For main_dev()
            #download_urls(urls, self.title, self.streams[stream_id]['container'], self.streams[stream_id]['size'])
        keep_obj = kwargs.get('keep_obj', False)
        if not keep_obj:
            self.__init__()
