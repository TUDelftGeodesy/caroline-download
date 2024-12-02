# download.py

import logging

# Setup logging 'library-style':
# Add null handle so we do nothing by default. It's up to whatever
# imports us, if they want logging.
# For more information, see:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def download(download_config, geo_search=None, product_search=None):
    logger.info('Starting download')
    logger.info(f"Download configuration: {download_config}")

    if geo_search:
        logger.info(f"Geo search: {geo_search}")

    if product_search:
        logger.info(f"Product search: {product_search}")
