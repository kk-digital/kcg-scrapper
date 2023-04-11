# Steam Apps Scrapy Project

Scrapy project to scrape steam apps and save html in warc format, extract apps data and media.

Coded and tested on python version 3.11.2.

## Installation

Create and environment and run:

`pip install -r requirements.txt`

If you're on windows and have problems running the spider, run:

`pip install python-magic-bin`

## How to run:

All commands described below must be run in the project's root.

### 1. Create jobs database

⚠️ Make sure to run it only once before starting the scraping job because purges the database, loosing all jobs state
data.

The database is already provided but if you need to re-create it with up to date steam apps data, just
replace the `steamcmd_appid.json` file and run:

`python steam_scraping/create_json_db.py`

Jobs have the following fields:

1. appid
2. name
3. status
    - pending: (default)
    - partial: some media content failed to be downloaded/saved
    - complete
    - failed
4. err_msg: in case of partial or failed

### 2. Start scraping

`scrapy crawl apps`

The spider scrape jobs marked as pending by default, you can modify this behavior passing arguments to spider:

- retryfailed=true
- retrypartial=true

`scrapy crawl apps -a retryfailed=true`

There is also a test mode that randomly picks 100 apps:

`scrapy crawl apps -a testmode=true`

Notice that the number of scraped pages may be lower than the number of apps in the db since many app ids are not valid,
causing steam redirecting to the homepage.

## Storage

Html is written to warc file only if response is in 200 range.

Extracted app data have the following fields:

- app_id: int
- game_title: str
- publisher: str
- developer: str
- publish_date: float|str = timestamp|'Coming soon...'
- tags: list
- images_path: list
- videos_path: list

Warc files are saved to `files/warc-files`, media content to `files/media/<app_id>`

### Export format

In `settings.py` you can modify everything related to the file in which the extracted data is stored:

```py
FEEDS = {'data.jsonl': {  # name of file
    'format': 'jsonl',
    'encoding': 'utf8',
    'store_empty': True,
    'fields': ['app_id', 'game_title', 'publisher', 'developer', 'publish_date', 'tags', 'images_path', 'videos_path'],
    'indent': 4,
    # whether overwrite or append
    'overwrite': False
}}
```