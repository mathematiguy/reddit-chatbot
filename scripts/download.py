#! /bin/python3
import os
import re
import argparse
import requests
import logging
import subprocess
from lxml import etree
from urllib.parse import urljoin
from utils import multicore_apply, sha256, timeit

def get_file_list(base_url):
	download_regex = re.compile("\./RC_[0-9]{4}-[0-9]{2}\.[bz2|xz]")
	response = requests.get(base_url)
	file_list = (etree
		.HTML(response.text)
		.xpath("/html/body/div/table/tbody/tr/td[1]/a/@href"))
	file_list = [f.rsplit("/", 1)[-1] for f in file_list if download_regex.match(f)]
	return file_list


def get_sha_hashes(hash_url, hash_path):
    response = requests.get(hash_url)
    hash_dict = {}
    with open(hash_path, "w") as f:
        for line in response.text.strip().split("\n"):
            sha256, filename = re.split("\s+", line, 1)
            hash_dict[filename] = sha256
            f.write(line + "\n")
    log.debug("sha256sum.txt saved to %s", hash_path)
    return hash_dict


def get_file_hashes(file_dir, limit):
    '''
    Build dict of sha256 sums of currently downloaded files
    '''
    zip_files = [os.path.join(file_dir, f) for num, f in enumerate(os.listdir(file_dir)) \
        if f.endswith(".xz") or f.endswith(".bz2") and \
           num < limit]
    zip_hashes = multicore_apply(zip_files, sha256)
    zip_names = [f.rsplit("/", 1)[-1] for f in zip_files]
    return dict(zip(zip_names, zip_hashes))


def wget_reddit_comments(url, output_path):
    cmd = ['wget', '--progress=dot:giga', url, '-O', output_path]
    log.info("Running: %s", " ".join(cmd))
    subprocess.call(cmd)

@timeit
def main():
    global log
    log = logging.getLogger(__name__)

    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base-url', help="The base url",
        default = "http://files.pushshift.io/reddit/comments/")
    parser.add_argument('-o', '--output-dir', help="The output directory",
        default = None)
    parser.add_argument('--limit', help="Limit files to hash (for testing)", type = int,
        default = float('inf'))
    parser.add_argument('--log-level', help="Log level", default = "INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format='[%(asctime)s] | line %(lineno)d | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S')

    args.limit = float('inf') if args.limit < 0 else args.limit

    file_list = get_file_list(args.base_url)

    sha_url = urljoin(args.base_url, "sha256sum.txt")
    sha_path = os.path.join(args.output_dir, "sha256sum.txt")
    log.debug("sha_url: %s", sha_url)
    log.debug("sha_path: %s", sha_path)

    log.info("Downloading remote hashes..")
    sha_hashes = get_sha_hashes(sha_url, sha_path)

    log.info("Hashing files..")
    file_hashes = get_file_hashes(args.output_dir, limit = args.limit)

    for file in file_list:
        target_path = os.path.join(args.output_dir, file)
        sha_hash = sha_hashes[file]
	    file_hash = file_hashes.get(file, "")
        if not os.path.exists(target_path) or sha_hash != file_hash:
            file_url = urljoin(args.base_url, file)
            output_path = os.path.join(args.output_dir, file)
            wget_reddit_comments(file_url, output_path)


if __name__ == "__main__":
    main()
