# download.py

import logging

# Setup logging 'library-style':
# Add null handle so we do nothing by default. It's up to whatever
# imports us, if they want logging.
# For more information, see:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
CAROLINE_DOWNLOAD_LOGGER = logging.getLogger(__name__)
CAROLINE_DOWNLOAD_LOGGER.addHandler(logging.NullHandler())

def download(download_config, geo_search=None, product_search=None):
    print(__name__)
    CAROLINE_DOWNLOAD_LOGGER.info('Starting download')
