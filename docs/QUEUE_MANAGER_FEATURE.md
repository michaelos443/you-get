# Batch Download Queue Manager

The **Batch Download Queue Manager** is a new feature for You-Get that allows users to queue multiple URLs for sequential downloading with pause/resume functionality.

## Overview

Instead of downloading URLs immediately, you can now add them to a persistent queue and process them later. This is particularly useful for:

- **Batch downloading**: Queue up multiple videos throughout the day and download them all at once
- **Bandwidth management**: Process downloads during off-peak hours when internet is faster
- **Interrupted downloads**: Resume queue processing after interruptions
- **Organized downloading**: Keep track of what you want to download without cluttering your terminal

## Features

- ✅ **Add URLs to queue** with custom download options
- ✅ **Process queue sequentially** with progress tracking
- ✅ **Persistent storage** - queue survives restarts
- ✅ **Status tracking** - pending, downloading, completed, failed
- ✅ **Error handling** - retry failed downloads
- ✅ **Queue management** - show, clear, remove completed items
- ✅ **Graceful interruption** - Ctrl+C pauses queue processing

## Usage

### Adding URLs to Queue

Add one or more URLs to the download queue:

```bash
# Add single URL
you-get --add-to-queue "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# Add multiple URLs
you-get --add-to-queue "https://www.youtube.com/watch?v=jNQXAC9IVRw" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Add URLs with specific options
you-get --add-to-queue --output-dir ~/Downloads --format mp4 "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

### Managing the Queue

View current queue status:
```bash
you-get --show-queue
```

Clear all items from queue:
```bash
you-get --clear-queue
```

Remove completed downloads from queue:
```bash
you-get --remove-completed
```

### Processing the Queue

Process all pending items in the queue:
```bash
# Process with default options
you-get --process-queue

# Process with specific options
you-get --process-queue --output-dir ~/Downloads --no-merge
```

## Queue Status Icons

The queue display uses intuitive icons to show the status of each item:

- ⏳ **PENDING** - Waiting to be downloaded
- ⬇️ **DOWNLOADING** - Currently being downloaded
- ✅ **COMPLETED** - Successfully downloaded
- ❌ **FAILED** - Download failed (with error message)
- ⏭️ **SKIPPED** - Manually skipped

## Queue File

The queue is automatically saved to `you_get_queue.json` in the current directory. This file contains:

- URL and download options for each item
- Status and attempt count
- Timestamps for when items were added/completed
- Error messages for failed downloads

## Examples

### Basic Workflow

```bash
# 1. Add some videos to queue throughout the day
you-get --add-to-queue "https://www.youtube.com/watch?v=video1"
you-get --add-to-queue "https://www.youtube.com/watch?v=video2"
you-get --add-to-queue "https://www.youtube.com/watch?v=video3"

# 2. Check what's in the queue
you-get --show-queue

# 3. Process all downloads at once (e.g., during off-peak hours)
you-get --process-queue --output-dir ~/Downloads

# 4. Clean up completed items
you-get --remove-completed
```

### Advanced Usage

```bash
# Add URLs with specific quality and format
you-get --add-to-queue --itag=22 --output-dir ~/Videos/HD "https://www.youtube.com/watch?v=video1"

# Process queue with info-only mode to check what would be downloaded
you-get --process-queue --info

# Process queue with specific player instead of downloading
you-get --process-queue --player vlc
```

## Error Handling

- **Failed downloads** are marked with ❌ and include error messages
- **Interrupted processing** (Ctrl+C) resets current item to pending for retry
- **Network errors** are caught and logged, allowing queue processing to continue
- **Invalid URLs** are marked as failed with appropriate error messages

## Integration with Existing Features

The queue manager integrates seamlessly with all existing You-Get features:

- **Download options**: All CLI options (format, quality, output directory, etc.) are preserved per URL
- **History tracking**: Queue downloads are recorded in download history
- **Progress bars**: Enhanced progress bars work during queue processing
- **Extractors**: All supported sites work with the queue system

## Technical Details

- **Queue persistence**: JSON file format for easy inspection and manual editing
- **Atomic operations**: Queue state is saved after each operation
- **Memory efficient**: Only loads queue data when needed
- **Thread-safe**: Safe for concurrent access (though not recommended)

## Limitations

- Queue processing is sequential (one download at a time)
- No priority system for queue items (FIFO order)
- No automatic retry mechanism for failed downloads
- Queue file location is fixed to current directory

## Future Enhancements

Potential improvements for future versions:

- **Priority queue**: Allow reordering of queue items
- **Parallel downloads**: Process multiple items simultaneously
- **Automatic retry**: Configurable retry attempts for failed downloads
- **Queue scheduling**: Time-based queue processing
- **Multiple queues**: Support for named/categorized queues
- **Web interface**: Browser-based queue management
