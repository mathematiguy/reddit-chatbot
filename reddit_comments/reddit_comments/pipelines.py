# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import os
import scrapy
import logging

logger = logging.getLogger()

class RedditCommentsPipeline(object):
    FILES_URLS_FIELD = 'file_urls'
    FILES_RESULT_FIELD = 'files'

    def process_item(self, item, spider):
        file_url = item["file_urls"]
        request = scrapy.Request(file_url)
        dfd = spider.crawler.engine.download(request, spider)
        dfd.addBoth(self.return_item, item)

    def return_item(self, response, item):
        if response.status != 200:
            # Error happened, return item.
            logger.debug("Bad response %s for item %s", response, item)

        # Save screenshot to file, filename will be hash of url.
        url = item["file_urls"]
        sha256 = item["sha256"]
        file_name = url.rsplit("/", 1)[-1]
        file_path = os.path.join("data", file_name)
        logger.debug(
            "url: %s file_name: %s sha256: %s file_path",
            url, file_name, sha256, file_path)

        if not os.path.exists(file_path) or sha256 != sha256(file_path):
            with open(file_path, "wb") as f:
                f.write(response.body)
            logger.info("Finished downloading %s", file_path)
