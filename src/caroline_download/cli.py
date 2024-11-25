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

LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s[%(process)d] - %(levelname)s - %(message)s'

def main():
    # Parse arguments

    # Create argument parser
    parser = argparse.ArgumentParser(
            prog=PROGRAM_NAME,
            description=f"{DESCRIPTION}",
            epilog=f"Author: {AUTHOR} <{AUTHOR_EMAIL}>"
            )

    # Add arguments to argument parser
    parser.add_argument('--config',
                        help='configuration file to use',
                        required=True
                        )
    parser.add_argument('--single-product',
                        help='download a single product'
                        )
    parser.add_argument('--redownload',
                        action='store_true',
                        help='force downloading, even if a product already exists'
                        )
    parser.add_argument('--log-file',
                        help='log to LOG_FILE'
                        )

    # Parse arguments and store result in args variable
    args = parser.parse_args()

    # Build configuration
    config = get_config(args)

    # Setup logging
    logger = logging.getLogger(PROGRAM_NAME)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    console_log = logging.StreamHandler(sys.stdout)
    console_log.setLevel(LOG_LEVEL)
    console_log.setFormatter(formatter)
    logger.addHandler(console_log)

    # Log to file if requested from command line
    if args.log_file:
        try:
            file_log = TimedRotatingFileHandler(args.log_file,
                                                when='midnight',
                                                backupCount=31
                                                )
            file_log.setLevel(LOG_LEVEL)
            file_log.setFormatter(formatter)
            logger.addHandler(file_log)
        except Exception as err:
            # Abort if we cannot create the log file as requested
            logger.fatal(f"Failed to create log file {args.log_file}. Reason: {err}. Aborting.")
            sys.exit(1)

    logger.info(f"Starting {PROGRAM_NAME}"
                f" v{importlib.metadata.version('caroline-download')}")
    logger.info(f"Configuration: {config}")

    download(config, logger)
    
# Eof
