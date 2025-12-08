#!/usr/bin/env python
"""Base extractor classes for video downloading.

This module provides:
    - Extractor: Minimal base class for simple extractors.
    - VideoExtractor: Full-featured base class with stream handling.
"""

import os
import sys

from .common import (
    maybe_print, download_urls, get_filename, parse_host,
    set_proxy, unset_proxy, dry_run, player
)
from .common import print_more_compatible as print
from .util import log
from . import json_output


def _init_base_attributes(obj, url=None):
    """Initialize common attributes for extractor classes.

    Args:
        obj: The extractor instance to initialize.
        url: Optional URL to set.
    """
    obj.url = url
    obj.title = None
    obj.vid = None
    obj.streams = {}
    obj.streams_sorted = []


class Extractor():
    """Minimal base class for simple extractors.

    Attributes:
        url: The source URL.
        title: The content title.
        vid: The video ID.
        streams: Dict of available streams.
        streams_sorted: List of streams sorted by quality.
    """

    def __init__(self, *args):
        """Initialize the extractor.

        Args:
            *args: Optional URL as first argument.
        """
        _init_base_attributes(self, args[0] if args else None)


class VideoExtractor():
    """Full-featured base class for video extractors.

    Provides stream management, download handling, and output formatting.

    Attributes:
        url: The source URL.
        title: The content title.
        vid: The video ID.
        m3u8_url: HLS manifest URL if applicable.
        streams: Dict of available streams.
        streams_sorted: List of streams sorted by quality.
        audiolang: Available audio languages.
        password_protected: Whether content requires password.
        dash_streams: Dict of DASH streams.
        caption_tracks: Dict of caption tracks by language.
        out: Flag indicating early exit.
        ua: Custom User-Agent header.
        referer: Custom Referer header.
        danmaku: Danmaku/comments data.
        lyrics: Lyrics data.
    """

    def __init__(self, *args):
        """Initialize the video extractor.

        Args:
            *args: Optional URL as first argument.
        """
        _init_base_attributes(self, args[0] if args else None)
        self.m3u8_url = None
        self.audiolang = None
        self.password_protected = False
        self.dash_streams = {}
        self.caption_tracks = {}
        self.out = False
        self.ua = None
        self.referer = None
        self.danmaku = None
        self.lyrics = None

    def _sort_streams(self):
        """Sort streams by quality based on stream_types ordering."""
        try:
            self.streams_sorted = [
                dict([('id', st['id'])] +
                     list(self.streams[st['id']].items()))
                for st in self.__class__.stream_types
                if st['id'] in self.streams
            ]
        except KeyError:
            self.streams_sorted = [
                dict([('itag', st['itag'])] +
                     list(self.streams[st['itag']].items()))
                for st in self.__class__.stream_types
                if st['itag'] in self.streams
            ]

    def _run_download(self, **kwargs):
        """Execute the prepare, extract, and download pipeline.

        Args:
            **kwargs: Download options passed to each step.
        """
        extractor_proxy = kwargs.get('extractor_proxy')
        if extractor_proxy:
            set_proxy(parse_host(extractor_proxy))

        self.prepare(**kwargs)

        if extractor_proxy:
            unset_proxy()

        if self.out:
            return

        self._sort_streams()
        self.extract(**kwargs)
        self.download(**kwargs)

    def download_by_url(self, url, **kwargs):
        """Download video by URL.

        Args:
            url: The video URL.
            **kwargs: Download options.
        """
        self.url = url
        self.vid = None
        self._run_download(**kwargs)

    def download_by_vid(self, vid, **kwargs):
        """Download video by video ID.

        Args:
            vid: The video ID.
            **kwargs: Download options.
        """
        self.url = None
        self.vid = vid
        self._run_download(**kwargs)

    def prepare(self, **kwargs):
        """Prepare for download. Override in subclasses."""
        pass

    def extract(self, **kwargs):
        """Extract stream information. Override in subclasses."""
        pass

    def _get_stream(self, stream_id):
        """Get stream info from streams or dash_streams.

        Args:
            stream_id: The stream identifier.

        Returns:
            The stream dictionary.
        """
        if stream_id in self.streams:
            return self.streams[stream_id]
        return self.dash_streams[stream_id]

    def _get_stream_id_key(self, stream):
        """Get the stream ID key ('id' or 'itag').

        Args:
            stream: The stream dictionary.

        Returns:
            The stream ID value.
        """
        return stream['id'] if 'id' in stream else stream['itag']

    def p_stream(self, stream_id):
        """Print stream information.

        Args:
            stream_id: The stream identifier to print.
        """
        stream = self._get_stream(stream_id)

        if 'itag' in stream:
            print("    - itag:          %s" %
                  log.sprint(stream_id, log.NEGATIVE))
        else:
            print("    - format:        %s" %
                  log.sprint(stream_id, log.NEGATIVE))

        if 'container' in stream:
            print("      container:     %s" % stream['container'])

        if 'video_profile' in stream:
            maybe_print("      video-profile: %s" % stream['video_profile'])

        if 'quality' in stream:
            print("      quality:       %s" % stream['quality'])

        if 'size' in stream and 'container' in stream:
            if stream['container'].lower() != 'm3u8':
                if stream['size'] != float('inf') and stream['size'] != 0:
                    size_mib = round(stream['size'] / 1048576, 1)
                    print("      size:          %s MiB (%s bytes)" %
                          (size_mib, stream['size']))

        if 'm3u8_url' in stream:
            print("      m3u8_url:      {}".format(stream['m3u8_url']))

        if 'itag' in stream:
            cmd = "you-get --itag=%s [URL]" % stream_id
            print("    # download-with: %s" %
                  log.sprint(cmd, log.UNDERLINE))
        else:
            cmd = "you-get --format=%s [URL]" % stream_id
            print("    # download-with: %s" %
                  log.sprint(cmd, log.UNDERLINE))

        print()

    def p_i(self, stream_id):
        """Print minimal stream info (index mode).

        Args:
            stream_id: The stream identifier.
        """
        stream = self._get_stream(stream_id)
        size_mib = round(stream['size'] / 1048576, 1)

        maybe_print("    - title:         %s" % self.title)
        print("       size:         %s MiB (%s bytes)" %
              (size_mib, stream['size']))
        print("        url:         %s" % self.url)
        print()

        sys.stdout.flush()

    def _select_best_stream_id(self):
        """Select the best stream ID from sorted streams.

        Returns:
            The best stream ID.
        """
        return self._get_stream_id_key(self.streams_sorted[0])

    def p(self, stream_id=None):
        """Print video information.

        Args:
            stream_id: Stream to print. None for best, [] for all.
        """
        maybe_print("site:                %s" % self.__class__.name)
        maybe_print("title:               %s" % self.title)

        if stream_id:
            print("stream:")
            self.p_stream(stream_id)

        elif stream_id is None:
            print("stream:              # Best quality")
            stream_id = self._select_best_stream_id()
            self.p_stream(stream_id)

        elif stream_id == []:
            print("streams:             # Available quality and codecs")
            if self.dash_streams:
                print("    [ DASH ] %s" % ('_' * 36))
                itags = sorted(
                    self.dash_streams,
                    key=lambda i: -self.dash_streams[i]['size']
                )
                for stream in itags:
                    self.p_stream(stream)
            if self.streams_sorted:
                print("    [ DEFAULT ] %s" % ('_' * 33))
                for stream in self.streams_sorted:
                    self.p_stream(self._get_stream_id_key(stream))

        if self.audiolang:
            print("audio-languages:")
            for i in self.audiolang:
                print("    - lang:          {}".format(i['lang']))
                print("      download-url:  {}\n".format(i['url']))

        sys.stdout.flush()

    def p_playlist(self, stream_id=None):
        """Print playlist information.

        Args:
            stream_id: Optional stream identifier (unused).
        """
        maybe_print("site:                %s" % self.__class__.name)
        print("playlist:            %s" % self.title)
        print("videos:")

    def _save_auxiliary_files(self, output_dir):
        """Save danmaku and lyrics files if available.

        Args:
            output_dir: The output directory path.
        """
        if self.danmaku is not None and not dry_run:
            filename = '{}.cmt.xml'.format(get_filename(self.title))
            print('Downloading {} ...\n'.format(filename))
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf8') as fp:
                fp.write(self.danmaku)

        if self.lyrics is not None and not dry_run:
            filename = '{}.lrc'.format(get_filename(self.title))
            print('Downloading {} ...\n'.format(filename))
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf8') as fp:
                fp.write(self.lyrics)

    def download(self, **kwargs):
        """Download the video or display information.

        Args:
            **kwargs: Download options including:
                json_output: Output as JSON.
                info_only: Only display info, don't download.
                stream_id: Specific stream to download.
                index: Use index mode display.
                output_dir: Output directory.
                merge: Merge video parts.
                caption: Download captions.
        """
        if kwargs.get('json_output'):
            json_output.output(self)
        elif kwargs.get('info_only'):
            stream_id = kwargs.get('stream_id')
            if stream_id:
                if 'index' not in kwargs:
                    self.p(stream_id)
                else:
                    self.p_i(stream_id)
            else:
                if 'index' not in kwargs:
                    self.p([])
                else:
                    stream_id = self._select_best_stream_id()
                    self.p_i(stream_id)

        else:
            stream_id = kwargs.get('stream_id')
            if not stream_id:
                # Download stream with the best quality
                from .processor.ffmpeg import has_ffmpeg_installed
                use_dash = (
                    has_ffmpeg_installed() and
                    player is None and
                    self.dash_streams
                ) or not self.streams_sorted

                if use_dash:
                    itags = sorted(
                        self.dash_streams,
                        key=lambda i: -self.dash_streams[i]['size']
                    )
                    stream_id = itags[0]
                else:
                    stream_id = self._select_best_stream_id()

            if 'index' not in kwargs:
                self.p(stream_id)
            else:
                self.p_i(stream_id)

            stream = self._get_stream(stream_id)
            urls = stream['src']
            ext = stream['container']
            total_size = stream['size']

            if ext in ('m3u8', 'm4a'):
                ext = 'mp4'

            if not urls:
                log.wtf('[Failed] Cannot extract video source.')

            headers = {}
            if self.ua is not None:
                headers['User-Agent'] = self.ua
            if self.referer is not None:
                headers['Referer'] = self.referer

            download_urls(
                urls, self.title, ext, total_size, headers=headers,
                output_dir=kwargs['output_dir'],
                merge=kwargs['merge'],
                av=stream_id in self.dash_streams,
                vid=self.vid
            )

            if not kwargs.get('caption'):
                print('Skipping captions or danmaku.')
                return

            for lang in self.caption_tracks:
                filename = '%s.%s.srt' % (get_filename(self.title), lang)
                print('Saving %s ... ' % filename, end="", flush=True)
                srt = self.caption_tracks[lang]
                filepath = os.path.join(kwargs['output_dir'], filename)
                with open(filepath, 'w', encoding='utf-8') as x:
                    x.write(srt)
                print('Done.')

            self._save_auxiliary_files(kwargs['output_dir'])

        if not kwargs.get('keep_obj', False):
            self.__init__()
