# -*- coding: utf-8 -*-
import os
import re
import requests
import hashlib
import scrapy
import logging
from utils import sha256, multicore_apply

logger = logging.getLogger()

def get_sha_hashes(hash_url):
    response = requests.get(hash_url)
    hash_dict = {}
    with open("data/sha256sum.txt", "w") as f:
        logger.debug("Writing sha256sum.txt to disk")
        for line in response.text.strip().split("\n"):
            sha256, filename = re.split("\s+", line, 1)
            hash_dict[filename] = sha256
            f.write(line + "\n")
    logger.info("sha256sum.txt saved to disk")
    return hash_dict

def get_file_hashes():
    '''
    Build dict of sha256 sums of currently downloaded files
    '''
    zip_files = [os.path.join("data", f) for f in os.listdir("data") if f.endswith(".xz") or f.endswith(".bz2")]
    zip_hashes = multicore_apply(zip_files, sha256)
    zip_names = [f.rsplit("/", 1)[-1] for f in zip_files]
    return dict(zip(zip_names, zip_hashes))

class DownloadSpider(scrapy.Spider):
    name = 'download'
    allowed_domains = ['files.pushshift.io/reddit/comments']
    start_urls = ['http://files.pushshift.io/reddit/comments/']

    def parse(self, response):
        download_urls = response.xpath("/html/body/div/table/tbody/tr/td[1]/a/@href").extract()
        download_regex = re.compile("\./RC_[0-9]{4}-[0-9]{2}\.[bz2|xz]")
        
        # Start by downloading the hash file
        sha_hashes = get_sha_hashes(response.urljoin("sha256sum.txt"))

        # Hash the local files
        file_hashes = get_file_hashes()

        # Then start downloading the other files
        for url in download_urls:
            if download_regex.match(url):
                file_name = url.rsplit("/", 1)[-1]
                file_path = os.path.join("data", file_name)
                try:
                    file_hash = ""
                    if os.path.exists(file_path):
                        sha_hash  = sha_hashes[file_name]
                        file_hash = file_hashes[file_name]
                except KeyError:
                    sha_hash = "missing"
                    logger.info("%s has no hash recorded in sha256sum.txt", file_name)
                if not os.path.exists(file_path) or sha_hash != file_hash:
                    logger.debug("file_url %s, file_name %s, sha_hash %s", 
                                 url,          file_name,    sha_hash)
                    yield {
                    	'file_urls': response.urljoin(url),
                        'file_name': file_name,
                    	'sha256': sha_hash 
                        }
                else:
                    logger.info("Skipped %s due to matching hash", file_name)
