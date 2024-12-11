# setup_icons.py
import requests
import os
from pathlib import Path


def download_icon(url: str, filename: str):
    icons_dir = Path("static/icons")
    icons_dir.mkdir(parents=True, exist_ok=True)

    response = requests.get(url)
    if response.status_code == 200:
        with open(icons_dir / filename, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {filename}")
    else:
        print(f"Failed to download: {filename}")


def setup_icons():
    # Font Awesome CDN icons (free version)
    icons = {
        'file.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file.svg',
        'image.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/image.svg',
        'document.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-alt.svg',
        'pdf.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-pdf.svg',
        'video.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-video.svg',
        'audio.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-audio.svg',
        'word.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-word.svg',
        'excel.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-excel.svg',
        'archive.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-archive.svg',
        'code.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/regular/file-code.svg'
    }

    for filename, url in icons.items():
        download_icon(url, filename)


if __name__ == "__main__":
    setup_icons()