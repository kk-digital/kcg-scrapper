## About The Project

Selenium automation to scrape pins from pinterest based on a query.

Workflow:

1. collect boards for query
2. collect pins for each board in previous step
3. download original pin img and save pin page source html
4. compress output in `MAX_OUTPUT_SIZE_MB` archives

## Getting Started

### Prerequisites

* python version 3.11.3
* google-chrome binaries

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
   pip install -r requirements.py
   ```

## Usage

The `command.py` is a cli with the following commands:

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

### Global parameters

- `headed` type boolean, default=0: whether to show browser GUI
- `max-workers` type integer, default=1: number of workers to concurrently scrape
- `output` type string, default='./output': path to store the output files
- `proxy-list` type string, default=None: path to proxy list csv file

### Notes

* can also use flags syntax for positional arguments, e.g.:
   ```sh
  python command.py start-scraping --query=cachicamo
  ```
* get help and more info for a command by passing `--help`
* can fine-tune details in the `settings.py` file, each entry is documented
