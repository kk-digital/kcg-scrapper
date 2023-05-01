## About The Project

Selenium automation to scrape pins from pinterest based on a query.

Workflow:

1. collect boards for query
2. collect pins for each board in previous step
3. download original pin img and save pin page source html
4. compress output in 500 MB archives

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
3. crete virutal environment:
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

The `command.py` is a cli with the following commnds:

* `show-jobs`
   ```sh
   python command.py  show-jobs
   ```

Show jobs info, including query and current stage.

* `delete-job <query>`
   ```sh
  python command.py delete-job t-shirts
  ```

⚠️⚠️⚠️ Be careful. Find and delete the jobs that matches the provided query, loosing current state of all boards/pins
already scraped.

* `test-scrape-board <url> [--headed] [output]`

   ```sh
  python command.py test-scrape-board --headed --output='~/test/output' https://www.pinterest.com/wilsonpercussio/cachicamo/
  ```

Scrape single board por testing purposes.

* `start-scraping <query> [--headed] [output]`

   ```sh
  python command.py start-scraping cachicamo 
  ```

Start scraping the query provided. Job is implicitly created if not exists. If exists, job is continued where left in
case of pause or error.

### Notes

* if output is not provided will default to `./output`
* can also use flags syntax for positional arguments, e.g.:
   ```sh
  python command.py start-scraping --query=cachicamo
  ```
* get help and more info for a command by passing `--help`
* can fine-tune details in the `settings.py` file, each entry is documented
