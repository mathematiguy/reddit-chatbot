# -*- coding: utf-8 -*-
import os
import re
import requests
import hashlib
import scrapy
import logging

logger = logging.getLogger()

def get_hashes(hash_url):
    response = requests.get(hash_url)
    with open("data/sha256sum.txt", "w") as f:
        logger.debug("Writing sha256sum.txt to disk")
        f.write(response.text)
    logger.info("sha256sum.txt saved to disk")

def get_hash_dict():
    hash_dict = {}
    with open("data/sha256sum.txt") as f:
        for line in f.read().strip().split("\n"):
            sha256, filename = re.split("\s+", line, 1)
            hash_dict[filename] = sha256
    return hash_dict

def sha256(filepath):
    hash_sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

class DownloadSpider(scrapy.Spider):
    name = 'download'
    allowed_domains = ['files.pushshift.io/reddit/comments']
    start_urls = ['http://files.pushshift.io/reddit/comments/']

    def parse(self, response):
        download_urls = response.xpath("/html/body/div/table/tbody/tr/td[1]/a/@href").extract()
        download_regex = re.compile("\./RC_[0-9]{4}-[0-9]{2}\.[bz2|xz]")
        
        # Start by downloading the hash file
        # Set priority so this downloads first
        logger.debug("Getting hashes..")
        get_hashes(
            response.urljoin('sha256sum.txt')
            )
        hash_dict = get_hash_dict()

        # Then start downloading the other files
        for url in download_urls:
            if download_regex.match(url):
                file_name = url.rsplit("/", 1)[-1]
                file_path = os.path.join("data", file_name)
                file_hash = hash_dict[file_name] if os.path.exists(file_path) else ""
                if not os.path.exists(file_path) or file_hash != sha256(file_path):
                    logger.debug("file_url %s, file_name %s, file_hash %s", 
                                 url,          file_name,    file_hash)
                    yield {
                    	'file_urls': response.urljoin(url),
                    	'sha256': file_hash 
                    }
                else:
                    logger.info("Skipped %s due to matching hash", file_name)
