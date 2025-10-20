# Quiet Mode Feature

## Overview
The Quiet Mode feature allows users to suppress non-essential output when using you-get, making it ideal for scripting, automation, and situations where minimal console output is desired.

## Usage

### Command-Line Flag
```bash
you-get -q <URL>
# or
you-get --quiet <URL>
```

### Examples

#### Basic Usage
```bash
# Download a video with minimal output
you-get --quiet https://www.youtube.com/watch?v=jNQXAC9IVRw
```

#### Scripting Example
```bash
#!/bin/bash
# Download multiple videos silently
for url in $(cat urls.txt); do
    you-get --quiet "$url"
done
```

#### Combined with Other Options
```bash
# Quiet mode with output directory
you-get -q -o ~/Downloads https://example.com/video

# Quiet mode with format selection
you-get --quiet --format=mp4 https://example.com/video
```

## Behavior

When quiet mode is enabled:

1. **Progress Bars**: All progress bars are suppressed (uses `DummyProgressBar`)
2. **Informational Logs**: Info messages are not displayed
3. **Debug Messages**: Debug output is suppressed
4. **Warning Messages**: Warnings are not shown
5. **Error Messages**: Errors are still displayed (critical for debugging)

## Implementation Details

### Global Variable
The feature uses a global `quiet` variable in `src/you_get/common.py`:
```python
quiet = False  # Default value
```

### CLI Argument
Defined in the argument parser:
```python
download_grp.add_argument('-q', '--quiet', action='store_true', default=False,
    help='Suppress non-error output (no logs, no progress bar)')
```

### Log Suppression
When quiet mode is activated:
```python
if args.quiet:
    quiet = True
    # Suppress info/debug/warning logs
    from .util import log as _log
    _log.i = lambda *a, **k: None
    _log.d = lambda *a, **k: None
    _log.w = lambda *a, **k: None
```

### Progress Bar Selection
The progress bar is replaced with a dummy implementation:
```python
if quiet:
    bar = DummyProgressBar()
elif enhanced_progress:
    bar = EnhancedProgressBar(total_size, len(urls))
else:
    bar = SimpleProgressBar(total_size, len(urls))
```

## Use Cases

1. **Automated Scripts**: Run you-get in cron jobs or automated workflows without cluttering logs
2. **Batch Downloads**: Download multiple files with minimal console noise
3. **CI/CD Pipelines**: Integrate you-get into build pipelines with clean output
4. **Background Processes**: Run downloads in the background without visual feedback
5. **Log File Management**: Reduce log file sizes when output is redirected

## Compatibility

- Works with all download modes (single file, playlist, etc.)
- Compatible with all output options (`-o`, `-O`, etc.)
- Can be combined with format selection (`--format`, `--itag`)
- Works alongside proxy settings (`-x`, `-y`)
- Compatible with cookie loading (`-c`)

## Related Features

- `--debug` (opposite behavior - shows more output)
- `--info` (dry-run mode with information display)
- `--json` (structured output format)
- `--enhanced-progress` (enhanced progress bar - disabled in quiet mode)

## Notes

- Error messages are intentionally NOT suppressed to ensure critical issues are visible
- The feature is designed to be minimally invasive to existing code
- Quiet mode takes precedence over enhanced progress mode
- Standard output redirection still works: `you-get -q URL > /dev/null 2>&1`

