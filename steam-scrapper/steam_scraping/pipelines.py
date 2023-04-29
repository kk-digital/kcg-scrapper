import json
import os
import urllib
import urllib.parse
from os import path
from pathlib import PurePosixPath

from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline

from steam_scraping.db import db


def is_video(path_str: str):
    return True if path_str.endswith(".mp4") or path_str.endswith(".gif") else False


class MyFilesPipeline(FilesPipeline):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.DOWNLOAD_VIDEOS = None
        self.test_mode = None
        self.STORE_URI = None

    def open_spider(self, spider):
        super().open_spider(spider)
        self.STORE_URI = spider.settings["FILES_STORE"]
        self.DOWNLOAD_VIDEOS = spider.settings["DOWNLOAD_VIDEOS"]
        self.test_mode = spider.test_mode

    def file_path(self, request, response=None, info=None, *, item=None):
        adapter = ItemAdapter(item)
        filename = PurePosixPath(urllib.parse.urlparse(request.url).path).name
        return f'{adapter["app_id"]}/{filename}'

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        file_urls = adapter.get("file_urls")

        if file_urls is None:
            return

        for file_url in file_urls:
            filename = PurePosixPath(urllib.parse.urlparse(file_url).path).name

            if is_video(filename) and not self.DOWNLOAD_VIDEOS:
                continue

            yield Request(file_url, meta={"is_resource": True})

    def item_completed(self, results, item, info):
        adapter = ItemAdapter(item)
        all_ok = all([result[0] for result in results])
        if all_ok and self.test_mode is None:
            self.db.update_by_id(adapter["db_id"], {"status": "complete"})

        images_path = []
        videos_path = []
        for ok, info_or_failure in results:
            if not ok:
                continue

            file_path = path.basename(info_or_failure["path"])

            if is_video(file_path):
                videos_path.append(file_path)
                continue
            images_path.append(file_path)

        adapter["images_path"] = images_path
        adapter["videos_path"] = videos_path

        return item


class SetDefaultPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for key in item.fields:
            adapter.setdefault(key, None)

        return item


class SaveItemAsJSONPipeline:
    def __init__(self):
        self.FILES_STORE = None

    def open_spider(self, spider):
        self.FILES_STORE = spider.settings["FILES_STORE"]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        app_id = adapter["app_id"]
        app_path = path.join(self.FILES_STORE, str(app_id))
        os.makedirs(app_path, exist_ok=True)

        json_path = path.join(app_path, f"data.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(adapter.asdict(), fh)

        return item
