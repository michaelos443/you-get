# Optimize you-get modules using better data structures

## Summary
The you-get codebase currently uses several basic data structures that could be optimized for better performance and maintainability. This task involves analyzing and refactoring the code to use more efficient data structures.

## Current Issues
* Simple dictionaries are used extensively for stream data storage without proper typing or structure
* Lists are used for URL storage where sets might be more appropriate in some cases
* Progress tracking uses simple classes that could benefit from more efficient data structures
* JSON handling could be optimized with better structured objects

## Proposed Changes
* Replace dictionary-based stream storage with proper classes/dataclasses
* Use more appropriate collections (e.g., defaultdict, Counter, OrderedDict) where applicable
* Implement proper type hints throughout the codebase
* Optimize the progress tracking classes with more efficient data structures
* Consider using namedtuples or dataclasses for structured data instead of plain dictionaries

## Key Files to Modify
* src/you_get/common.py - Contains core data structures and utility functions
* src/you_get/extractor.py - Base classes for extractors that use dictionary-based storage
* src/you_get/json_output.py - JSON handling that could benefit from structured data
* Various extractor modules in src/you_get/extractors/

## Expected Benefits
* Improved code readability and maintainability
* Better performance for large downloads and playlists
* Reduced memory usage
* Easier extension of the codebase with new features

## Implementation Details

### 1. Stream Data Structure Improvements
Current implementation in extractor.py uses dictionaries:
```python
self.streams = {}
self.streams_sorted = []
```

Proposed change to use dataclasses:
```python
@dataclass
class Stream:
    id: str
    container: str
    size: int
    src: List[str]
    quality: str = "__default__"
    # Additional fields as needed
    
# Then in VideoExtractor
self.streams: Dict[str, Stream] = {}
self.streams_sorted: List[Stream] = []
```

### 2. Progress Tracking Optimization
Current implementation has multiple progress bar classes with duplicated code. Consider using a single class with different display strategies.

### 3. URL Collection Handling
For URL collections where order doesn't matter and duplicates should be avoided, use sets instead of lists:
```python
# Before
urls = []
for line in m3u8_list:
    if line and not line.startswith('#'):
        urls.append(line)

# After
urls = set()
for line in m3u8_list:
    if line and not line.startswith('#'):
        urls.add(line)
```

### 4. JSON Output Improvements
Replace the current approach in json_output.py with structured classes that can be serialized to JSON.

## Priority
Medium

## Labels
optimization, refactoring, performance
