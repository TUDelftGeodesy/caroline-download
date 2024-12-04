# cli.py

import argparse
import importlib.metadata
import logging
from logging.handlers import TimedRotatingFileHandler
import sys

from caroline_download.config import get_config
from caroline_download.download import download

PROGRAM_NAME = 'caroline-download'

AUTHOR = 'Niels Jansen'
AUTHOR_EMAIL = 'n.h.jansen[at]tudelft.nl'

DESCRIPTION = """
Download data for processing with CAROLINE

Currently only downloads SENTINEL-1 SLC products from
ASF (Alaska Satellite Facility) with authentication using .netrc
"""


def main():

    # Parse arguments and store result in args variable
    args = parse_args()

    # Build configuration
    config = get_config(args=args)

    # Setup logging
    logger = setup_logging(log_config=config.logging)

    logger.info(f"Starting {PROGRAM_NAME}"
                f" v{importlib.metadata.version('caroline-download')}")
    logger.debug(f"Configuration: {config}")

    download(download_config=config.download,
             geo_search=config.geo_search,
             product_search=config.product_search,
             )


def parse_args():
    # Create argument parser
    parser = argparse.ArgumentParser(
            prog=PROGRAM_NAME,
            description=f"{DESCRIPTION}",
            epilog=f"Author: {AUTHOR} <{AUTHOR_EMAIL}>"
            )

    # Add arguments to argument parser
    parser.add_argument(
            '--config',
            help='configuration file to use',
            )
    parser.add_argument(
            '--geo-search',
            help='download based on geo search',
            )
    parser.add_argument(
            '--product-search',
            help='download a single product'
            )
    parser.add_argument(
            '--force',
            action='store_true',
            help='force downloading, even if a product already exists locally'
            )
    parser.add_argument(
            '--verify',
            action='store_true',
            help='verify checksum after downloading'
            )
    parser.add_argument(
            '--dry-run',
            action='store_true',
            help='perform dry run. do not actually download anything'
            )
    parser.add_argument(
            '--log-file',
            help='log to LOG_FILE'
            )
    parser.add_argument(
            '--log-level',
            help='set log level'
            )
    parser.add_argument(
            '--quiet',
            action='store_true',
            help='do not log anything to stderr'
            )

    return parser.parse_args()


def setup_logging(log_config):
    console_log = logging.StreamHandler(sys.stdout)
    console_log_format = logging.Formatter(log_config.console_log.format)
    console_log.setLevel(log_config.console_log.level.value)
    console_log.setFormatter(console_log_format)

    if log_config.file_log.file:
        try:
            file_log = TimedRotatingFileHandler(log_config.file_log.file,
                                                when='midnight',
                                                backupCount=31
                                                )
            file_log_format = logging.Formatter(log_config.file_log.format)
            file_log.setLevel(log_config.file_log.level.value)
            file_log.setFormatter(file_log_format)
        except Exception as err:
            # Abort if we cannot create the log file as requested
            print("Failed to create log file. "
                  + f"Reason: {err}. Aborting.",
                  file=sys.stderr)
            sys.exit(1)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_config.console_log.level.value)
    root_logger.addHandler(console_log)
    if log_config.file_log.file:
        root_logger.addHandler(file_log)

    logger = logging.getLogger(PROGRAM_NAME)
    logger.setLevel(log_config.console_log.level.value)
    logger.propagate = False
    logger.addHandler(console_log)
    if log_config.file_log.file:
        logger.addHandler(file_log)

    download_logger = logging.getLogger('caroline_download.download')
    download_logger.setLevel(log_config.console_log.level.value)
    download_logger.propagate = False
    download_logger.addHandler(console_log)
    if log_config.file_log.file:
        download_logger.addHandler(file_log)

    asf_logger = logging.getLogger('asf-search')
    asf_logger.setLevel(log_config.console_log.level.value)
    asf_logger.propagate = False
    asf_logger.addHandler(console_log)
    if log_config.file_log.file:
        asf_logger.addHandler(file_log)

    return logger

# Eof
