# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from datetime import datetime

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Identity, Compose
from scrapy import Field
from scrapy.loader import ItemLoader


def get_timestamp(str_date):
    try:
        date = datetime.strptime(str_date, '%d %b, %Y')
        return datetime.timestamp(date)
    except ValueError:
        return str_date


class AppItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    app_id = Field()
    db_id = Field()
    game_title = Field()
    publisher = Field()
    developer = Field()
    publish_date = Field()
    tags = Field()
    file_urls = Field()
    images_path = Field()
    videos_path = Field()


class AppLoader(ItemLoader):
    default_output_processor = TakeFirst()
    default_input_processor = TakeFirst()
    default_item_class = AppItem

    publish_date_in = Compose(TakeFirst(), get_timestamp)
    tags_in = MapCompose(str.strip)
    tags_out = Identity()
    file_urls_in = Identity()
    file_urls_out = Identity()
