# Pull Request: Add Wikipedia extractor to extract article content as Markdown

## Description

This PR adds a new extractor for Wikipedia that allows users to extract and save article content in Markdown format. This is useful for offline reading, research, or creating local archives of Wikipedia articles.

## Features

- Extract text content from Wikipedia articles
- Save content as Markdown files
- Preserve headings and paragraph structure
- Clean up unwanted elements (references, edit links, etc.)

## Changes

- Added new `wikipedia.py` extractor module
- Updated SITES dictionary in common.py
- Updated extractors/__init__.py to include the new module
- Added BeautifulSoup4 as a dependency in requirements.txt and setup.py
- Updated README.md with documentation for the new feature

## Example Usage

```
$ you-get https://en.wikipedia.org/wiki/Free_software
Site:       Wikipedia
Title:      Free software
Type:       Markdown
Size:       0.12 MiB (123456 Bytes)

Wikipedia article saved to: Free software.md
```
