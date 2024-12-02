# config.py

# Implementation based on suggestions from:
# https://tech.preferred.jp/en/blog/working-with-configuration-in-python/

import datetime
from dataclasses import dataclass
import logging
from typing import List
from typing import Optional
from enum import Enum
import os
import pathlib
import sys

import dacite
import dateparser
import yaml

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = ('%(asctime)s'
                      + ' - %(name)s'
                      + '[%(process)d]'
                      + ' - %(levelname)s'
                      + ' - %(message)s'
                      )

class LogLevel(Enum):
    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NOTSET = logging.NOTSET

@dataclass 
class GeoSearch:
    start: datetime.datetime
    end: datetime.datetime
    roi_wkt_file: pathlib.Path
    relative_orbits: List[int]

@dataclass 
class Download:
    dest_dir: pathlib.Path
    force: bool = False
    dry_run: Optional[bool] = False

@dataclass
class ConsoleLog:
    enable: bool = True
    level: LogLevel = LogLevel[DEFAULT_LOG_LEVEL]
    format: str = DEFAULT_LOG_FORMAT

@dataclass
class FileLog:
    file: Optional[pathlib.Path]
    level: LogLevel = LogLevel[DEFAULT_LOG_LEVEL]
    format: str = DEFAULT_LOG_FORMAT

@dataclass
class Log:
    console_log: ConsoleLog = ConsoleLog(
                            enable=True,
                            level=LogLevel[DEFAULT_LOG_LEVEL],
                            format=DEFAULT_LOG_FORMAT
                            )
    file_log: FileLog = FileLog(
                        file=None,
                        level=LogLevel[DEFAULT_LOG_LEVEL],
                        format=DEFAULT_LOG_FORMAT
                        )

@dataclass 
class Config:
    download: Download
    geo_search: Optional[GeoSearch]
    product_search: Optional[str]
    logging: Log = Log(
                   console_log=ConsoleLog(
                               enable=True,
                               level=LogLevel[DEFAULT_LOG_LEVEL],
                               format=DEFAULT_LOG_FORMAT
                               ),
                   file_log=FileLog(
                       file=None,
                       level=LogLevel[DEFAULT_LOG_LEVEL],
                       format=DEFAULT_LOG_FORMAT
                       )
               )

converters = {
        pathlib.Path: pathlib.Path,
        datetime.datetime: lambda x: dateparser.parse(x),
        LogLevel: lambda x: LogLevel[x]
        }

def get_config(args):

    config_dict = {}
    config_file = None

    # Check that either config dir is set in environment or
    # config argument is used
    if not any((os.environ.get('CAROLINE_DOWNLOAD_CONFIG_DIR'),
                args.config)):
        print('ERROR: No configuration specified. Aborting.', file=sys.stderr)
        sys.exit(1)

    # If CONFIG_DIR is set, set config file to 
    # CONFIG_DIR/caroline_download.yaml
    if os.environ.get('CAROLINE_DOWNLOAD_CONFIG_DIR'):
        config_file = os.path.join(
                os.environ['CAROLINE_DOWNLOAD_CONFIG_DIR'],
                'caroline-download.yaml'
                )
    # If config argument is used, use that config file in stead
    if args.config:
        config_file = args.config

    # Check that the config file exists before we read it
    if not os.path.exists(config_file):
        # Config file does not exist
        print(f'ERROR: File not found: {config_file}', file=sys.stderr)
        sys.exit(1)

    # Open config file and read into config_dict
    with open(config_file, 'r') as config_file:
        config_dict = yaml.safe_load(config_file)

    if not any((args.geo_search, args.product_search)):
        print('ERROR: You must use either the --geo-search '
              + 'or the --product option.',
              file=sys.stderr
              )
        sys.exit(1)

    if args.geo_search:
        # Read yaml specified in argument and merge in config_dict
        if os.path.exists(args.geo_search):
            with open(args.geo_search, 'r') as geo_search_file:
                geo_search_dict = yaml.safe_load(geo_search_file)
            config_dict.update(geo_search_dict)
        else:
            print(f"File not found: {args.geo_search}", file=sys.stderr)
            sys.exit(1)

    config = dacite.from_dict(data_class=Config,
                              data=config_dict,
                              config=dacite.Config(type_hooks=converters)
                              )

    if args.product_search:
        config.product_search = args.product_search

    if args.force:
        config.download.force = True

    if args.dry_run:
        config.download.dry_run = True

    if args.log_file:
        config.logging.file_log.file = args.log_file

    if args.log_level:
        config.logging.console_log.level = LogLevel[args.log_level.upper()]

    if args.quiet:
        config.logging.console_log.level = LogLevel['NOTSET']

    if not config.geo_search.roi_wkt_file.exists():
        print(f"ERROR: No such file: {config.geo_search.roi_wkt_file}",
              file=sys.stderr
              )
        sys.exit(1)

    return config
