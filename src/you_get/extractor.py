#!/usr/bin/env python

"""Common extractor base classes for you-get.

This module defines the shared interfaces and behaviours used by concrete
site-specific extractors. It focuses on:

* representing basic video metadata (URL, title, ID, streams)
* providing helper methods for printing video information
* orchestrating the prepare/extract/download lifecycle
"""

import os
import sys
from typing import Any, Dict, List, Optional, Union

from .common import (
    dry_run,
    download_urls,
    get_filename,
    match1,
    maybe_print,
    parse_host,
    player,
    set_proxy,
    unset_proxy,
    get_content,
)
from .common import print_more_compatible as print
from .util import log
from . import json_output


class Extractor:
    """Base class for all extractors.

    This class provides basic properties and methods for extracting video information.
    It is designed to be extended by specific site extractors.
    """

    def __init__(self, *args: str) -> None:
        """Initialize the extractor with an optional URL.

        Parameters
        ----------
        *args
            Variable length argument list. If provided, the first argument is
            treated as the URL associated with this extractor instance.
        """
        self.url: Optional[str] = None
        self.title: Optional[str] = None
        self.vid: Optional[str] = None
        self.streams: Dict[str, Dict[str, Any]] = {}
        self.streams_sorted: List[Dict[str, Any]] = []

        if args:
            self.url = args[0]


class VideoExtractor(Extractor):
    """Base class for video extractors.

    This class extends the basic Extractor with video-specific properties and methods.
    It provides functionality for downloading videos, handling streams, and displaying
    video information.
    """

    def __init__(self, *args: str) -> None:
        """Initialize the video extractor with an optional URL.

        Parameters
        ----------
        *args
            Variable length argument list. If provided, the first argument is
            treated as the URL associated with this extractor instance.
        """
        super().__init__(*args)
        self.m3u8_url: Optional[str] = None
        self.audiolang: Optional[List[Dict[str, str]]] = None
        self.password_protected: bool = False
        self.dash_streams: Dict[str, Dict[str, Any]] = {}
        self.caption_tracks: Dict[str, str] = {}
        self.out: bool = False
        self.ua: Optional[str] = None
        self.referer: Optional[str] = None
        self.danmaku: Optional[str] = None
        self.lyrics: Optional[str] = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _prepare_with_proxy(self, **kwargs: Any) -> None:
        """Run :meth:`prepare` while respecting an optional extractor proxy.

        The ``extractor_proxy`` keyword argument is interpreted in the same
        way as in the original implementation: when present and truthy, the
        proxy is enabled only for the duration of :meth:`prepare`.
        """
        proxy = kwargs.get("extractor_proxy")
        if proxy:
            set_proxy(parse_host(proxy))

        try:
            self.prepare(**kwargs)
        finally:
            if proxy:
                unset_proxy()

    def _build_streams_sorted(self) -> None:
        """Populate :attr:`streams_sorted` based on available stream types.

        The method mirrors the original ``try/except`` behaviour that first
        prefers an ``"id"`` key in ``stream_types`` and falls back to
        ``"itag"`` for legacy extractors.
        """
        self.streams_sorted = []

        stream_types = getattr(self.__class__, "stream_types", [])
        if not stream_types:
            return

        def _build_for_key(key: str) -> List[Dict[str, Any]]:
            results: List[Dict[str, Any]] = []
            for stream_type in stream_types:
                stream_id = stream_type.get(key)
                if stream_id is None or stream_id not in self.streams:
                    continue

                stream_info = self.streams[stream_id]
                merged: Dict[str, Any] = {key: stream_id}
                merged.update(stream_info)
                results.append(merged)
            return results

        # Prefer modern ``id``-based stream types, fall back to ``itag``
        # to preserve compatibility with older extractors.
        streams_sorted = _build_for_key("id")
        if not streams_sorted:
            streams_sorted = _build_for_key("itag")

        self.streams_sorted = streams_sorted

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
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

        self._prepare_with_proxy(**kwargs)
        if self.out:
            return

        self._build_streams_sorted()
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

        self._prepare_with_proxy(**kwargs)
        self._build_streams_sorted()
        self.extract(**kwargs)

        self.download(**kwargs)

    def prepare(self, **kwargs: Any) -> None:
        """Prepare for extraction.

        Subclasses should override this method to perform any site-specific
        work required before extraction. Typical responsibilities include
        fetching metadata, resolving playlist or video IDs, and populating
        ``self.streams`` or ``self.dash_streams``.

        Parameters
        ----------
        **kwargs
            Arbitrary keyword arguments forwarded from the high-level
            ``download_*`` helpers.
        """
        pass
        # raise NotImplementedError()

    def extract(self, **kwargs: Any) -> None:
        """Extract video streams.

        Subclasses should override this method to populate ``self.streams`` and
        optionally ``self.dash_streams`` with concrete download URLs and
        metadata.

        Parameters
        ----------
        **kwargs
            Arbitrary keyword arguments forwarded from the high-level
            ``download_*`` helpers.
        """
        pass
        # raise NotImplementedError()

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

        if (
            'size' in stream
            and 'container' in stream
            and stream['container'].lower() != 'm3u8'
        ):
            if stream['size'] not in (float('inf'), 0):
                size_mib = round(stream['size'] / 1048576, 1)
                print(
                    "      size:          %s MiB (%s bytes)"
                    % (size_mib, stream['size'])
                )

        if 'm3u8_url' in stream:
            print(f"      m3u8_url:      {stream['m3u8_url']}")

        if 'itag' in stream:
            print(
                "    # download-with: %s"
                % log.sprint(
                    "you-get --itag=%s [URL]" % stream_id,
                    log.UNDERLINE,
                )
            )
        else:
            print(
                "    # download-with: %s"
                % log.sprint(
                    "you-get --format=%s [URL]" % stream_id,
                    log.UNDERLINE,
                )
            )

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
        print(
            "       size:         %s MiB (%s bytes)"
            % (round(stream['size'] / 1048576, 1), stream['size'])
        )
        print("        url:         %s" % self.url)
        print()

        sys.stdout.flush()

    def p(self, stream_id: Optional[Union[str, List]] = None) -> None:
        """Print video information.

        This method prints information about the current video and one or more
        of its streams.

        Parameters
        ----------
        stream_id
            The ID of the stream to print information for. When ``None`` the
            best-quality stream is printed. When an empty list, all available
            streams are printed.
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
                itags = sorted(
                    self.dash_streams,
                    key=lambda i: -self.dash_streams[i]['size'],
                )
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
                print(f"    - lang:          {i['lang']}")
                print(f"      download-url:  {i['url']}\n")

        sys.stdout.flush()

    def p_playlist(self, stream_id: Optional[str] = None) -> None:
        """Print playlist-level information.

        Parameters
        ----------
        stream_id
            Reserved for future use; currently ignored.
        """
        maybe_print("site:                %s" % self.__class__.name)
        print("playlist:            %s" % self.title)
        print("videos:")

    def download(self, **kwargs: Any) -> None:
        """Download the video.

        This method handles the actual downloading of the video using the
        extracted stream information. It also supports an "info only" mode
        and optional caption and auxiliary file downloads.

        Parameters
        ----------
        **kwargs
            Keyword arguments that control the download behaviour. Common
            options include:

            ``json_output``
                When true, emit JSON instead of human-readable output.
            ``info_only``
                When true, display information without downloading.
            ``stream_id``
                Explicit ID of the stream to download.
            ``index``
                When true, use the compact display format.
            ``output_dir``
                Directory where downloaded files are stored.
            ``merge``
                Whether to merge multiple parts after download.
            ``caption``
                Whether to download caption tracks when available.
            ``keep_obj``
                When false (default) reinitialise the extractor instance
                after the download finishes.
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

                if (
                    (
                        has_ffmpeg_installed()
                        and player is None
                        and self.dash_streams
                    )
                    or not self.streams_sorted
                ):
                    itags = sorted(
                        self.dash_streams,
                        key=lambda i: -self.dash_streams[i]['size'],
                    )
                    stream_id = itags[0]
                else:
                    stream_id = (
                        self.streams_sorted[0]['id']
                        if 'id' in self.streams_sorted[0]
                        else self.streams_sorted[0]['itag']
                    )

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

            if ext in {'m3u8', 'm4a'}:
                ext = 'mp4'

            if not urls:
                log.wtf('[Failed] Cannot extract video source.')
            # For legacy main()
            headers = {}
            if self.ua is not None:
                headers['User-Agent'] = self.ua
            if self.referer is not None:
                headers['Referer'] = self.referer
            download_urls(
                urls,
                self.title,
                ext,
                total_size,
                headers=headers,
                output_dir=kwargs['output_dir'],
                merge=kwargs['merge'],
                av=stream_id in self.dash_streams,
                vid=self.vid,
            )

            if 'caption' not in kwargs or not kwargs['caption']:
                print('Skipping captions or danmaku.')
                return

            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print(f'Saving {filename} ... ', end="", flush=True)
                srt = self.caption_tracks[lang]
                with open(os.path.join(kwargs['output_dir'], filename),
                          'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')

            if self.danmaku is not None and not dry_run:
                filename = f"{get_filename(self.title)}.cmt.xml"
                print(f'Downloading {filename} ...\n')
                with open(
                    os.path.join(kwargs['output_dir'], filename),
                    'w',
                    encoding='utf8',
                ) as fp:
                    fp.write(self.danmaku)

            if self.lyrics is not None and not dry_run:
                filename = f"{get_filename(self.title)}.lrc"
                print(f'Downloading {filename} ...\n')
                with open(
                    os.path.join(kwargs['output_dir'], filename),
                    'w',
                    encoding='utf8',
                ) as fp:
                    fp.write(self.lyrics)

            # For main_dev()
            #download_urls(urls, self.title, self.streams[stream_id]['container'], self.streams[stream_id]['size'])
        keep_obj = kwargs.get('keep_obj', False)
        if not keep_obj:
            self.__init__()
