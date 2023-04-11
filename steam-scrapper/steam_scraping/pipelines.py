from os import path
from pathlib import PurePosixPath
from urllib.parse import urlparse

from itemadapter import ItemAdapter
from scrapy import Request
from scrapy.pipelines.files import FilesPipeline

from steam_scraping.db import db


class MyFilesPipeline(FilesPipeline):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.STORE_URI = args[0]
        self.test_mode = None

    def open_spider(self, spider):
        self.test_mode = spider.test_mode
        super().open_spider(spider)

    def file_path(self, request, response=None, info=None, *, item=None):
        adapter = ItemAdapter(item)
        return f'{adapter["app_id"]}/{PurePosixPath(urlparse(request.url).path).name}'

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        file_urls = adapter.get('file_urls')

        for file_url in file_urls:
            yield Request(file_url, meta={'is_resource': True})

    def item_completed(self, results, item, info):
        adapter = ItemAdapter(item)
        all_ok = all([result[0] for result in results])
        if all_ok and self.test_mode is None:
            self.db.update_by_id(adapter['db_id'], {'status': 'complete'})

        images_path = []
        videos_path = []
        for ok, info_or_failure in results:
            if not ok:
                continue

            file_path = info_or_failure['path']
            is_mp4 = file_path.endswith('.mp4')
            file_path = path.normpath(path.join(self.STORE_URI, file_path))

            if is_mp4:
                videos_path.append(file_path)
                continue
            images_path.append(file_path)

        adapter['images_path'] = images_path
        adapter['videos_path'] = videos_path

        return item
