from scrapy.exceptions import DropItem


class CheckImagesPipeline:
    def process_item(self, item: dict, spider):
        images = item.get("images", None)
        if images is None or not images:
            raise DropItem("Item contains no images")

        return item
