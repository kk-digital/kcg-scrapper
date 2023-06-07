## About the project

Scrape and stores images using official Civitai API.

The project consists of two stages:

1. traverse list of images provided by the api, saving to db images data to later download
2. download the images saved is last step and append images data to json db

Images and output in general are saved by default to `/output` in the container, mount there to persist output.

Change output location and other settings in `settings.py`. Each entry is documented.

### Installation

1. build docker image:
   ```sh
   docker build -t civitai .
   ```
2. run container:
   ```sh
   docker run -d -t --name civitai civitai
   ```
5. get inside container:
   ```sh
   docker exec -it civitai bash
   ```

## Usage

`command.py` is a cli with the commands described below.

---

`start-scraping`

```sh
python command.py start-scraping
```

Create job and start to scrape.

---

`delete-output`

```sh
python command.py delete-output
```

⚠️ Delete db and output folder.

---
