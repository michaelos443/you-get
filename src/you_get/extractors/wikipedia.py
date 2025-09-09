#!/usr/bin/env python

__all__ = ['wikipedia_download']

from ..common import *
import json
import re
from html import unescape
from bs4 import BeautifulSoup

def wikipedia_download(url, output_dir='.', merge=True, info_only=False, **kwargs):
    """Download text content from Wikipedia pages.
    
    Args:
        url: The URL of the Wikipedia page
        output_dir: The directory to save the downloaded file
        merge: Whether to merge video parts
        info_only: Whether to just print the information without downloading
    """
    # Get the HTML content of the Wikipedia page
    html = get_html(url)
    
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Extract the title of the Wikipedia page
    title = soup.find('h1', {'id': 'firstHeading'}).text.strip()
    
    # Extract the main content of the Wikipedia page
    content_div = soup.find('div', {'id': 'mw-content-text'})
    
    # Remove unwanted elements
    for unwanted in content_div.select('.mw-editsection, .reference, .noprint, .mw-empty-elt, .mw-headline-anchor'):
        unwanted.decompose()
    
    # Extract paragraphs and headings
    paragraphs = []
    for element in content_div.select('p, h2, h3, h4, h5, h6'):
        if element.name.startswith('h'):
            # Format headings with appropriate level of '#'
            level = int(element.name[1])
            heading_text = element.get_text().strip()
            if heading_text and not heading_text.startswith('[') and len(heading_text) > 1:
                paragraphs.append('\n' + '#' * level + ' ' + heading_text + '\n')
        else:
            # Regular paragraph
            text = element.get_text().strip()
            if text:
                paragraphs.append(text + '\n')
    
    # Join all paragraphs into a single text
    text_content = '\n'.join(paragraphs)
    
    # Clean up the text (remove excessive newlines, etc.)
    text_content = re.sub(r'\n{3,}', '\n\n', text_content)
    
    # Create a filename from the title
    filename = get_filename(title)
    filepath = os.path.join(output_dir, filename + '.md')
    
    # Print information about the download
    print_info('Wikipedia', title, 'Markdown', len(text_content.encode('utf-8')))
    
    if not info_only:
        # Write the content to a Markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text_content)
        
        print(f'Wikipedia article saved to: {filepath}')

site_info = "Wikipedia"
download = wikipedia_download
download_playlist = playlist_not_supported('wikipedia')
