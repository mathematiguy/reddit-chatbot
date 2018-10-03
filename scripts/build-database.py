#! /bin/python3
import os
import re
import json
import yaml
import argparse
import logging
import subprocess
from py2neo import Graph
from utils import md5_string
from _mysql import escape_string

global log
log = logging.getLogger(__name__)

JSON_KEYS = ['author', 'author_flair_css_class', 'author_flair_text', 'body', 
    'controversiality', 'created_utc', 'distinguished', 'edited', 'gilded', 'id', 
    'link_id', 'parent_id', 'retrieved_on', 'score', 'stickied', 'subreddit', 
    'subreddit_id', 'ups']
log.debug("line_dict keys: %s", ', '.join(JSON_KEYS))


def read_credentials(credentials_path):
    with open(credentials_path, "r") as f:
        text = f.read()
        creds = yaml.load(text)
    return creds


def test_keys(line_dict, line_num):
    # Test keys match
    if sorted(line_dict.keys()) != JSON_KEYS:
        raise ValueError("Keys do not match on line {}: {}".format(line_num, ', '.join(sorted(line_dict.keys()))))


def clean_json(record_json):
    for k, v in record_json.items():
        if k == "body":
            record_json[k] = escape_string(v).decode('utf-8')
        if k == "author":
            author_id = md5_string(v.encode('utf-8'))
            record_json[k] = v
        if v is None:
            record_json[k] = "null"
    record_json['author_id'] = author_id
    return record_json


def create_record(*args, **kwargs):
    query = '''
    // Create subreddit
    CREATE ({subreddit_id}:Subreddit {{name:'{subreddit}'}})
    
    // Create link
    CREATE ({link_id}:Link)
    
    // Create Author
    CREATE ({author_id}:Author {{name: '{author}'}})
    
    // Create comment
    CREATE ({id}:Comment {{
            body:'{body}',
            controversiality:{controversiality},
            gilded:{gilded},
            edited:{edited},
            distinguished:{distinguished},
            retrieved_on:{retrieved_on},
            ups:{ups}
            }})
    
    // Create parent comment
    MERGE ({parent_id}:Comment)

    // Link post to the subreddit
    CREATE ({link_id})-[:POSTED_IN]->({subreddit_id})
    CREATE ({id})-[:POSTED_IN]->({link_id})
    CREATE (author)-[:WROTE {{created_utc:{created_utc}}}]->({id})
    CREATE ({id})-[:CHILD_OF]->({parent_id})
    '''.format(**clean_json(kwargs))
    return query


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', help="The comments file to parse",
        default = None)
    parser.add_argument('--credentials-path', help="The path to credentials.yaml",
        default = 'scripts/credentials.yaml')
    parser.add_argument('--from-scratch', help="Delete all nodes before running", action="store_true")
    parser.add_argument('--limit', help="Max number of rows to process", type = int, 
        default = float("inf"))
    parser.add_argument('--log-level', help="Log level", default = "INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format='[%(asctime)s] | line %(lineno)d | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S')

    creds = read_credentials(args.credentials_path)['neo4j']
    db_uri = "http://{username}:{password}@{host}:{port}/db/data/".format(**creds)
    log.debug("db_uri: %s", db_uri)
    graph = Graph(db_uri)

    if args.from_scratch:
        log.info("Deleting database contents..")
        graph.run('''
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE n, r
            ''')

    log.info("About to read %s", args.file)
    with open(args.file, "r") as f:
        for i, line in enumerate(f):
            # Read the line to a dict
            line_dict = json.loads(line)
            
            # Test the dict keys are what we expect
            test_keys(line_dict, i + 1)

            # Running Cypher query
            log.info("Running cypher query")
            query = create_record(**line_dict)
            log.debug(query)
            graph.run(query)

            if i + 1 >= args.limit:
                break



if __name__ == "__main__":
    main()
