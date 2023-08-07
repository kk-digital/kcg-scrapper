# Kemono Scraper

Scrapy project to scrape Kemono website.

## Getting Started

### Prerequisites

- Create `proxy-list.txt` at the project's root with your proxies. This is required unless you disable proxy middleware.
  Follow `proxy-list-format.txt` example.

### Installation

1. Create a virtual environment in the project's root:
   ```sh
   python3 -m venv venv
   ```

2. Install dependencies:
   ```sh
    pip install -r requirements.txt
    ```

## Usage

- To start scraping run:
    ```sh
    scrapy crawl posts -O posts.jsonl
    ```

---

`command.py` contains a cli with the following commands:

- `compress-output`
    ```sh
    python command.py compress-output <jsonl-path>
    ```

Compress the images found in the given jsonl file.

---

In `kemono/settings.py` you can change the following settings:

- `OUTPUT_FOLDER`: folder where the files will be saved.
- `MAX_ARCHIVE_SIZE`: maximum size of the archives in bytes when compressing with the command `compress-output`.





