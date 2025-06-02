# Enhanced Batch Download Feature

## Overview

The enhanced batch download feature allows you to download multiple videos from a list of URLs with improved error handling, progress tracking, and retry mechanisms.

## Usage

### Basic Batch Download

Create a text file with URLs (one per line):

```
# urls.txt
https://www.youtube.com/watch?v=dQw4w9WgXcQ
https://www.youtube.com/watch?v=jNQXAC9IVRw
https://vimeo.com/123456789
```

Then run:

```bash
you-get -I urls.txt
```

### Advanced Options

#### Retry Failed Downloads

Set the maximum number of retries for failed downloads:

```bash
you-get -I urls.txt --max-retries 5
```

#### Combine with Other Options

You can combine batch download with other you-get options:

```bash
# Download to specific directory with retries
you-get -I urls.txt -o ~/Downloads --max-retries 3

# Get info only for all URLs
you-get -I urls.txt --info

# Force overwrite existing files
you-get -I urls.txt --force
```

## File Format

The input file supports:

- **URLs**: One URL per line
- **Comments**: Lines starting with `#` are ignored
- **Empty lines**: Blank lines are ignored

Example:
```
# My favorite videos
https://www.youtube.com/watch?v=dQw4w9WgXcQ

# Educational content
https://www.youtube.com/watch?v=jNQXAC9IVRw

# More videos here...
```

## Features

### Progress Tracking
- Shows current progress: `[2/5] Processing: https://...`
- Displays summary at the end with success/failure counts

### Error Handling
- Continues downloading other URLs even if one fails
- Configurable retry mechanism (default: 2 retries)
- Detailed error reporting in the summary

### Summary Report
```
Batch download summary:
  Total URLs: 5
  Successful: 4
  Failed: 1

Failed downloads:
  - https://example.com/broken-link: HTTP Error 404: Not Found
```

## Examples

### Download Multiple YouTube Videos
```bash
echo "https://www.youtube.com/watch?v=dQw4w9WgXcQ" > my_videos.txt
echo "https://www.youtube.com/watch?v=jNQXAC9IVRw" >> my_videos.txt
you-get -I my_videos.txt -o ~/Videos
```

### Batch Download with High Retry Count
```bash
you-get -I unreliable_urls.txt --max-retries 10
```

This feature is particularly useful for:
- Downloading video playlists from multiple platforms
- Batch processing of bookmarked videos
- Automated content archiving
- Handling unreliable network connections with retries
