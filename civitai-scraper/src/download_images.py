import json
import os
import urllib.parse
from os import path

import requests
from pathlib import PurePosixPath

import jsonlines

import settings
from src.client import Client
from src.db import DB


class ImageDownloader:
    def __init__(self, client: Client, db: DB) -> None:
        self._client = client
        self._db = db
        # init output folder and jsonl file
        os.makedirs(settings.FILES_STORE, exist_ok=True)
        json_location = path.join(settings.FILES_STORE, "data.jsonl")
        self._json_fp = jsonlines.open(json_location, "a")

    def close(self) -> None:
        self._json_fp.close()

    def _save_image(self, response: requests.Response, image_id: int) -> str:
        url_path = urllib.parse.urlparse(response.url).path
        original_basename = PurePosixPath(url_path).name
        ext = path.splitext(original_basename)[1]
        new_basename = f"{image_id}{ext}"
        file_path = path.join(settings.FILES_STORE, new_basename)
        with open(file_path, "wb") as fp:
            fp.write(response.content)

        return new_basename

    def _add_json_entry(self, image_name: str, image_data: dict):
        data = {"filename": image_name, **image_data}
        self._json_fp.write(data)

    def start_download(self) -> None:
        print("Downloading images...")
        for img in self._db.get_images():
            image_data = json.loads(img["response"])
            image_url = image_data["url"]
            image_id = image_data["id"]
            print(f"Downloading image id {image_id}.")
            try:
                response = self._client.make_request(image_url)
            # ignoring bc there is images that fail forever
            except requests.exceptions.HTTPError as e:
                if e.response.status_code >= 400:
                    continue
                else:
                    raise
            filename = self._save_image(response, image_id)
            self._add_json_entry(filename, image_data)
            self._db.update_image_status(image_id)

        print("Download finished.")
