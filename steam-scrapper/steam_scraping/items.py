# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re

import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Identity, Compose
from scrapy import Field
from scrapy.loader import ItemLoader

clean_review_count_processor = Compose(
    TakeFirst(), lambda reviews: re.sub(r"[(),]", "", reviews), int
)


class AppItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    app_id = Field()
    db_id = Field()
    url = Field()
    game_title = Field()
    publisher = Field()
    developer = Field()
    publish_date = Field()
    tags = Field()
    review_count = Field()
    positive_review_count = Field()
    negative_review_count = Field()
    file_urls = Field()
    images_path = Field()
    videos_path = Field()


class AppLoader(ItemLoader):
    default_output_processor = TakeFirst()
    default_input_processor = TakeFirst()
    default_item_class = AppItem

    tags_in = MapCompose(str.strip)
    tags_out = Identity()
    review_count_in = clean_review_count_processor
    positive_review_count_in = clean_review_count_processor
    negative_review_count_in = clean_review_count_processor
    file_urls_in = Identity()
    file_urls_out = Identity()
