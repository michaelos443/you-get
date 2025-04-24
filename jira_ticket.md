# Jira Ticket: Add Wikipedia extractor to extract article content as Markdown

## Project
SCRUM

## Issue Type
Story

## Priority
Medium

## Summary
Add Wikipedia extractor to extract article content as Markdown

## Description
This ticket is for adding a new extractor for Wikipedia that allows users to extract and save article content in Markdown format. This is useful for offline reading, research, or creating local archives of Wikipedia articles.

## Features

- Extract text content from Wikipedia articles
- Save content as Markdown files
- Preserve headings and paragraph structure
- Clean up unwanted elements (references, edit links, etc.)

## Implementation Details

- Added new wikipedia.py extractor module
- Updated SITES dictionary in common.py
- Updated extractors/__init__.py to include the new module
- Added BeautifulSoup4 as a dependency in requirements.txt and setup.py
- Updated README.md with documentation for the new feature

## Status
Completed

---
Co-authored by [Augment Code](https://www.augmentcode.com/?utm_source=atlassian&utm_medium=jira_issue&utm_campaign=jira)
