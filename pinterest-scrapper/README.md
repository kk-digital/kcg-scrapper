## About The Project

Selenium automation to scrape pins from pinterest based on a query.

Workflow:

1. collect boards for query
2. collect pins for each board in previous step
3. download original pin img and save pin page source html
4. compress output in `MAX_OUTPUT_SIZE_MB` archives

A proxy list can be provided, the scraper cycles through the proxy list, rotating every `PROXY_ROTATE_MINUTES`.

The number of workers to run can be specified. Each worker is an instance of a Chrome browser, so be careful of having
enough free ram, ~2 GB per worker. If using proxies, set workers to at most 25% of available proxies, so when the
scraper rotates it uses a not recently used proxy.

The output folder can be configured via cli parameters, otherwise defaults to project root `output` folder. On the other
hand, logs are always stored in `logs` folder in the root dir as well.

Most general configuration can be provided via cli parameters. For detailed control you can modify any entry in
the `settings.py` file; each entry is documented.

## Getting Started

### Prerequisites

- python version 3.11.3
- google-chrome binaries

  Download first:

  ```
  wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  ```

  Install:

  ```
  sudo dpkg -i google-chrome-stable_current_amd64.deb
  ```

### Installation

1. clone the repo
   ```sh
   git clone https://github.com/kk-digital/kcg-scrapper
   ```
2. change cwd:
   ```sh
   cd pinterest-scrapper
   ```
3. create virtual environment:
   ```sh
   python -m venv venv
   ```
4. activate env:
   ```sh
   source venv/bin/activate
   ```
5. install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

The `command.py` is a cli with commands described below.

### Global cli parameters

- `query-list` type string: name of the csv file with query list
- `headed` type boolean, default=0: whether to show browser GUI
- `max-workers` type integer, default=1: number of workers to concurrently scrape
- `output` type string, default='./output': path to store the output files
- `proxy-list` type string, default=None: path to proxy list csv file

---

`show-jobs`

```sh
python command.py  show-jobs
```

Show jobs info, including query and current stage.

---

`delete-job <query>`

```sh
python command.py delete-job t-shirts
```

⚠️⚠️⚠️ Be careful. Find and delete the jobs that matches the provided query, loosing current state of all boards/pins
already scraped.

#### Parameters

- `query` type string: query associated with job to delete

---

`test-scrape-board <url> [--headed] [max-workers] [output] [proxy-list]`

```sh
python command.py test-scrape-board --output='~/test/output' https://www.pinterest.com/wilsonpercussio/cachicamo/
```

Scrape single board por testing purposes.

#### Parameters

- `url` type string: board url to scrape

---

`start-scraping <query> [--headed] [max-workers] [output] [proxy-list]`

```sh
python command.py start-scraping --max-workers=4 cachicamo
```

Start scraping the query provided. Job is implicitly created if not exists. If exists, job is continued where left in
case of pause or error.

#### Parameters

- `query` type string: query to search boards and start scraping

---

`start-scraping-list <query-list> [--headed] [max-workers] [output] [proxy-list]`

Same as `start-scraping` but you can provide csv file with a list of queries. Make sure there is only one query per row.

```sh
python command.py start-scraping-list --max-workers=4 cachicamo
```

---

`board-search <query-list> [--headed] [output] [proxy-list]`

Provide a query list csv file and get a json file with overview information such as total board count, total unique board count, total pin count, query board count, query pin count, board url, board title, board pin count.

Note that all data found in this job is not stored in database. Also, this command doesn't have `max-workers` due to limitations. 

```sh
python command.py board-search --proxy-list=proxies.csv query-list.csv
```

---

### Notes

- can also use flags syntax for positional arguments, e.g.:
  ```sh
  python command.py start-scraping --query=cachicamo
  ```
- get help and more info for a command by passing `--help`
