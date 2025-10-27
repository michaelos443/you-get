# Download History & Resume Manager Feature

## Overview

The Download History & Resume Manager feature provides comprehensive tracking and management of download activities in you-get. It maintains a local SQLite database that records download progress, status, and metadata, enabling users to resume interrupted downloads and manage their download history effectively.

## Features

### 📊 Download History Tracking
- Automatically records all download attempts with metadata (URL, title, filename, size, status)
- Tracks download progress in real-time during active downloads
- Maintains timestamps for creation and last update
- Stores error messages for failed downloads

### 🔄 Resume Capability
- Resume interrupted downloads from the last saved progress point
- Automatic detection of partially downloaded files
- Retry mechanism for failed downloads with configurable retry limits
- Progress preservation across application restarts

### 📋 History Management
- View comprehensive download history with filtering options
- Clear download history when needed
- Retry multiple failed downloads in batch
- Status tracking (pending, completed, failed, interrupted)

## Usage

### Command Line Options

#### Show Download History
```bash
you-get --history
```
Displays the last 50 downloads with their status, progress, and metadata.

#### Resume a Download
```bash
you-get --resume "https://www.youtube.com/watch?v=VIDEO_ID"
```
Resumes a previously interrupted or failed download from where it left off.

#### Retry Failed Downloads
```bash
you-get --retry-failed
```
Automatically retries all failed downloads (up to 3 retry attempts per download).

#### Clear Download History
```bash
you-get --clear-history
```
Removes all download history after user confirmation.

### Examples

#### Basic Download with History Tracking
```bash
# Download a video (automatically tracked in history)
you-get "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# View download history
you-get --history
```

#### Resume Interrupted Download
```bash
# If a download gets interrupted, resume it
you-get --resume "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

#### Batch Retry Failed Downloads
```bash
# Retry all failed downloads
you-get --retry-failed
```

#### Scripting with History
```bash
#!/bin/bash
# Download multiple videos with error handling
urls=(
    "https://www.youtube.com/watch?v=VIDEO1"
    "https://www.youtube.com/watch?v=VIDEO2"
    "https://www.youtube.com/watch?v=VIDEO3"
)

for url in "${urls[@]}"; do
    echo "Downloading: $url"
    you-get --resume "$url" || echo "Failed to download: $url"
done

# Show final status
echo "Download history:"
you-get --history
```

## Database Schema

The feature uses SQLite database with the following schema:

```sql
CREATE TABLE downloads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    title TEXT,
    filename TEXT,
    file_path TEXT,
    total_size INTEGER,
    downloaded_size INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    url_hash TEXT UNIQUE,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT
);
```

## Database Location

The history database is stored at:
- **Windows**: `%USERPROFILE%\.you-get\history.db`
- **Linux/macOS**: `~/.you-get/history.db`

## Implementation Details

### Automatic Tracking
- Downloads are automatically tracked when using standard you-get commands
- Progress updates occur every 1MB during active downloads
- Status is updated to 'completed' when downloads finish successfully
- Status is updated to 'failed' when downloads encounter errors

### Resume Logic
- Checks for existing partial files (.download extension)
- Validates file size and progress consistency
- Automatically sets appropriate HTTP Range headers for resumption
- Updates retry count to prevent infinite retry loops

### Error Handling
- Captures and stores error messages for debugging
- Limits retry attempts to 3 per download by default
- Distinguishes between network errors, file system errors, and other failures
- Provides user-friendly error messages in history output

## Integration with Existing Features

### Quiet Mode
The history feature works seamlessly with `--quiet` mode:
```bash
you-get --quiet --resume "https://example.com/video.mp4"
```

### Enhanced Progress Bar
History tracking is compatible with the enhanced progress bar:
```bash
you-get --enhanced-progress "https://example.com/video.mp4"
```

### Output Directory
History respects custom output directories:
```bash
you-get -o ~/Downloads "https://example.com/video.mp4"
you-get --resume "https://example.com/video.mp4" -o ~/Downloads
```

## Performance Considerations

- Database operations are optimized for minimal impact on download performance
- Progress updates are batched (every 1MB) to reduce I/O overhead
- Database is automatically created on first use
- History queries are indexed for fast retrieval

## Troubleshooting

### History Not Showing Recent Downloads
- Ensure the download completed or was interrupted (not skipped due to existing file)
- Check that the database file exists and is writable
- Use `--debug` flag to see detailed error messages

### Resume Not Working
- Verify the partial file (.download) still exists
- Check that the original URL is accessible
- Ensure sufficient disk space for completion
- Try increasing retry count if limit was reached

### Database Corruption
- If the database becomes corrupted, you can safely delete it
- A new database will be created automatically on next use
- Download history will be lost but won't affect download functionality

## Security and Privacy

- History data is stored locally and never transmitted
- Database contains only download metadata, no content
- Users can clear history at any time
- Database file permissions follow system defaults

## Future Enhancements

Potential future improvements include:
- Export history to CSV/JSON formats
- Advanced filtering and search capabilities
- Integration with cloud storage for cross-device sync
- Bandwidth usage tracking and statistics
- Download scheduling and queue management
