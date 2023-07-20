## About the project

Scrape midjourney showcase using headless browser, download images with prompt.

The scraper is consists of two main stages, for first stage, data gathering, the workflow:

1. logs in to midjourney with credentials provided and navigates to "new" category in showcase section
2. select "grid" filter to scrape only grids
3. configure response interceptor to capture response from midjourney's grids API endpoint
4. starts scrolling while capturing and pushing to db the data obtained from API

Stops after number of scrolls desired is reached, and starts download stage, the workflow:

1. query db for images in download stage and proceeds with downloading
2. once all images are download, the scraper terminates. Repeat, or if happy with the amount scraped then run:

    1. `export-json-data`
    2. `compress-output`

Output is saved by default to `/output` in the container, mount there to persist output.

Proxy is disabled by default. To enable it, create a file similar to `proxy-list-example.csv`, place it in the container
and set the name of the file to env var `PROXY_LIST`. Worth nothing that discord ask for email verification each time a
log in occurs from a different IP, so make sure to confirm before running.

Change other settings in `settings.py`.

### Installation

1. build docker image:
   ```sh
   docker build -t midjourney .
   ```
2. run container:
   In order to configure the scraper, need to set the environment variables listed on dockerfile, which are:

* `PYTHON_ENV` default to production
* `OUTPUT_FOLDER` default to /output
* `LOGGING_LEVEL` default to INFO
* `HEADED` default to false - headed mode not possible on container since display not available.
* `DS_EMAIL` required - email to log into midjourney showcase
* `DS_PASSWORD` required - password to log in
* `PROXY_LIST` optional - name of the csv file with proxy list

  In development, create a .env file to set these variables.

    ```sh
    docker run -dt -e DS_EMAIL=youremail@service.com -e DS_PASSWORD=secretpassword --name midjourney midjourney
    ```

3. get inside container:
   ```sh
   docker exec -it midjourney bash
   ```

## Usage

`command.py` is a cli with the commands described below.

---

`start-scraping`

```sh
python command.py start-scraping
```

#### Parameters:

- `prompt-filter` optional string - single filter or sequence of filters comma separated. Only scrape generations where
  filter is in prompt. Example: `--prompt-filter='pixel art, white background'`
- `use-storage-stage` optional boolean - save and reuse authentication state

---

`export-json-data`

```sh
python command.py export-json-data
```

Exports to json file the data from images scraped till now, placed in output folder.

#### Parameters:

- `prompt-filter` optional string - if provided, only export to json generations whose prompt filter match with the one
  given at scraping time. Else exports all generations in completed status.
- `test-export` default false - if option enabled, generations in db are not marked as exported, so can be exported
  again.

---

`compress-output`

```sh
python command.py compress-output
```

Compress images into zips of size `MAX_ARCHIVE_SIZE`. Only files exported to json are compressed.

#### Parameters:

- `test-export` default false - if option enabled, original images are not deleted, so can be exported again.

---
