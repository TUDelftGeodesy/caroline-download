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
    config = get_config(args)

    # Setup logging
    logger = setup_logging(config)

    logger.info(f"Starting {PROGRAM_NAME}"
                f" v{importlib.metadata.version('caroline-download')}")
    logger.info(f"Configuration: {config}")

    download(config, logger)


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
            help='force downloading, even if a product already exists'
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


def setup_logging(config):
    logger = logging.getLogger(PROGRAM_NAME)
    logger.setLevel(config.log.console_log.level.value)
    logger.propagate = False

    formatter = logging.Formatter(config.log.console_log.format)

    console_log = logging.StreamHandler(sys.stdout)
    console_log.setLevel(config.log.console_log.level.value)
    console_log.setFormatter(formatter)
    logger.addHandler(console_log)

    # Log to file if requested from command line
    if config.log.file_log.file:
        try:
            file_log = TimedRotatingFileHandler(config.log.file_log.file,
                                                when='midnight',
                                                backupCount=31
                                                )
            file_log.setLevel(config.log.file_log.level.value)
            file_log.setFormatter(formatter)
            logger.addHandler(file_log)
        except Exception as err:
            # Abort if we cannot create the log file as requested
            logger.fatal(f"Failed to create log file {args.log_file}. "
                         + f"Reason: {err}. Aborting.")
            sys.exit(1)

    return logger


# Eof
