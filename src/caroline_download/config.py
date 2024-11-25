# config.py

# Implementation based on:
# https://tech.preferred.jp/en/blog/working-with-configuration-in-python/

import datetime
from dataclasses import dataclass
from typing import List
from typing import Optional
import pathlib
import sys

import dacite
import dateparser
import yaml

@dataclass 
class Query:
    start: datetime.datetime
    end: datetime.datetime
    roi: pathlib.Path
    relative_orbits: List[int]

@dataclass 
class Download:
    dest_dir: pathlib.Path
    query: Optional[Query]
    product: Optional[str]
    redownload: bool = False

@dataclass 
class Config:
    download: Download
                                                                               
converters = {
        pathlib.Path: pathlib.Path,
        datetime.datetime: lambda x: dateparser.parse(x)
        }

default_config = {
        'download': {
            'dest_dir': '',
            'query': {
                'start': '',
                'end': '',
                'roi': '',
                'relative_orbits': []
                },
            'product': '',
            'redownload': False
            }
        }

def get_config(args):
    with open(args.config, 'r') as config_file:
        config_dict = yaml.safe_load(config_file)

    if args.single_product:
        config_dict['download']['product'] = args.single_product

    if args.redownload:
        config_dict['download']['redownload'] = True

    config = dacite.from_dict(data_class=Config,
                              data=config_dict,
                              config=dacite.Config(type_hooks=converters)
                              )

    try:
        assert config.download.query.roi.exists()
    except AssertionError:
        print(f"No such file: {config.download.query.roi}")
        sys.exit(1)

    return config
