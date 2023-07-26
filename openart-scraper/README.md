## About The Project

Scrapy spider to scrape prompts and images from openart website.

## Getting started

### Prerequisites

- Create the file `proxy-list.txt` and place there your proxies. This is a required unless you disable proxy middleware.
  Follow `proxy-list-format.txt` example.

### Installation

1. Move to project root and create a virtual environment
   ```sh
   python3 -m venv venv
   ```

2. Install dependencies
   ```sh
    pip install -r requirements.txt
    ```

## Usage

- To run the scraper run:

```sh
scrapy crawl prompts -a query='pixel art' -O pixel-art.jsonl
```

Must provide the query as argument, use the `-a` flag followed by the argument like in the example. You must also indicate the file to output the data obtained, use the `-O` flag followed by the file name.

---

`command.py` is a cli with the following commands:

- `compress-output`
    ```sh
    python command.py compress-output <jsonl-path>
    ```

Compress the images found in the given jsonl file.
