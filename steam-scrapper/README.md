# Steam Apps Scrapy Project

Scrapy project to scrape steam apps and save html in warc format, extract apps data and media.

Output is stored by default in project's root output folder. Changes this in `settings.py`. Also, can compress output
folder with `compress-output` command after scraping is done or send over the red is needed.

## Installation

1. clone the repo
   ```sh
   git clone https://github.com/kk-digital/kcg-scrapper
   ```
2. change working directory:
   ```sh
   cd kcg-scrapper/steam-scrapper
   ```
3. build docker image:
   ```sh
   docker build -t steam .
   ```
4. run container:
   ```sh
   docker run -d -t -v .:/app --name steam steam
   ```
5. get inside container:
   ```sh
   docker exec -it steam bash
   ```

## How to run:

All commands described below must be run in the project's root.

### 1. Command utility

- #### clean-db-and-output:

⚠️The following command purge the db and delete the output folder:

`python command.py clean-db-and-output`

- #### extract-apps:

The database is already provided, but if you need to add more apps, use the following
command `extract-apps <file_name>`.

Place the file next to the command module and replace file_name with the name of the file, which can be any text based
file that contains steam app urls. It's decoded using utf-8 and the regex used to extract app ids
is `https://store\.steampowered\.com/app/(\d+)`. No duplicates are inserted.

`python command.py extract-apps data.html`

To gather app urls from multipe files into one file and feed the command above, use:

`grep -r store.steampowered.com/app *.html > results.txt`

Use `-r` to search in the current and children dirs.

Specify the files to search in such as `urls.csv` or `*.html` for all html files, or `*` for all files.

It'll store the entire lines matching the criteria into `results.txt`. Pass it to the command and let it do the work of
extracting the app ids.

The command extract the ids and insert jobs to the db with the following form:

1. appid
2. status:
    - pending: (default)
    - partial: some media content failed to be downloaded/saved
    - complete
    - failed
3. err_msg: in case of partial or failed

- #### compress-output:

Compress output, one zip per app id folder. Resulting zips are placed in the compressed-apps folder next to apps.

`python command.py compress-output`


### 2. Start scraping

To start scrapping, you must first know what db you're pulling jobs from. You can set the db name in settings by
modifying `JOBS_DB_NAME`.

There are two db provided. `JOBS_DB_NAME` is set by default to `small-apps-db.json`, which contains a selection of apps;
the other db provided is `apps-db.json` that contains almost 160,000 apps. Set it to the latter to use the big lis

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

## Settings

You can alter the behavior of certain parts of the scraper modifying the following settings in `settings.py`:

- `ROTATING_PROXY_LIST_PATH` proxy list csv file location
- `DOWNLOAD_VIDEOS` whether to download videos or gifs, default to `False`
- `OUTPUT_FOLDER` folder to store all outputs, default to `output` in the project root. You can set it to relative or
  absolute path such as:
    - `~/apps/output`
    - `C:\Users\<user>\Desktop\New folder`
- `JOBS_DB_NAME` database to pull jobs from


