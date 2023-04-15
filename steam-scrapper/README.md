# Steam Apps Scrapy Project

Scrapy project to scrape steam apps and save html in warc format, extract apps data and media.

Coded and tested on python version 3.11.2.

## Installation

Create and environment and run:

`pip install -r requirements.txt`

Just in case you're having problems to tun the spider, run:

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

To run the scrapper run:

`scrapy crawl apps`

If you run the scrapper with no arguments (DEFAULT), like above, only jobs marked in db as pending will be taken.

You can also provide arguments to the spider and modify the default behavior:

- `retryfailed=true` take jobs marked as 'failed'
- `retrypartial=true` take jobs marked as 'partial'

E.g: `scrapy crawl apps -a retryfailed=true`

There is also a test mode that randomly picks 100 apps:

`scrapy crawl apps -a testmode=true`

Redirect is disabled since many app ids are invalid,
causing steam redirecting to the homepage. Causing the amount of scrapped apps may be lower than the apps in db.

## Storage

Html is written to warc file only if response is in 200 range.

Extracted app data have the following fields:

- app_id: int
- url: str
- game_title: str
- publisher: str
- developer: str
- publish_date: str = date|'Coming soon...'
- tags: list
- review_count: int (all/total reviews count)
- positive_review_count: int
- negative_review_count: int
- images_path: list
- videos_path: list

Warc files are saved to `output/warc-files`, app data and media content to `output/apps/<app_id>`
