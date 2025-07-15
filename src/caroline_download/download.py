# download.py
"""Download."""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
import hashlib
import json
import logging
import os
import sys

import asf_search as asf

# TODO do not import eodag entirely, but only required modules as per their instructions
# see: https://eodag.readthedocs.io/en/stable/notebooks/api_user_guide/4_search.html
import eodag
from eodag.crunch import FilterProperty
import shapely

# Setup logging 'library-style':
# Add null handle so we do nothing by default. It's up to whatever
# imports us, if they want logging.
# For more information, see:
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
eodag.setup_logging(verbose=2, no_progress_bar=True)


def compose_product_download_path(
    base_directory, file_name, relative_orbit, orbit_direction, polarization
):
    """Compose product download path.

    Parameters
    ----------
    base_directory: str
        The base download directory
    file_name: str
        The name of the file to download
    relative_orbit: str
        The relative orbit of the product
    orbit_direction: str
        The orbit direction of the product
    polarization: str
        The polarization of the product

    Returns
    -------
    str
        A string representation of the composed path
    """
    # Log debugging information
    logger.debug("base_directory: %s.", base_directory)
    logger.debug("file_name: %s.", file_name)
    logger.debug("relative_orbit: %s.", relative_orbit)
    logger.debug("orbit_direction: %s.", orbit_direction)
    logger.debug("polarization: %s.", polarization)

    # Translate orbit direction from what we get from ASF API to what
    # we use in the path
    orbit_direction = {
        "ASCENDING": "asc",
        "DESCENDING": "dsc",
    }.get(orbit_direction)

    # Pad track number (relative_orbit) with leading zero's when it has
    # less than 3 characters
    relative_orbit = relative_orbit.zfill(3)

    # Extract dataset from filename
    dataset = file_name[4:16]

    # Remove '+' from polarization
    polarization = polarization.replace("+", "")

    # Get startdate from filename
    year = file_name[17:21]
    month = file_name[21:23]
    day = file_name[23:25]

    # Construct path from rewritten variables
    path = base_directory
    path = path.joinpath("s1_" + orbit_direction + "_t" + relative_orbit)
    path = path.joinpath(dataset + "_" + polarization)
    path = path.joinpath(year + month + day)

    logger.debug("directory path: %s.", path)

    # Return composed path
    return path


def download(download_config, geo_search=None, product_search=None):
    """Download.

    Parameters
    ----------
    download_config:
        download configuration
    geo_search:
        search configuration
    product_search:
        product name
    """
    logger.info("Starting download")
    logger.debug(f"Download configuration: {download_config}")

    if product_search:
        logger.info(f"Performing product search for product {product_search}")
        result = asf.product_search(product_search)
        product_count = len(result)

        if product_count > 1:
            logger.error(
                "Found more than one product while performing "
                "product search. This should not happen according "
                "to the ASF api documentation. Aborting."
            )
            sys.exit(1)

        logger.info(f"Found {str(product_count)} products")
        download_products(download_config, result)

    if geo_search:
        logger.info(f"Performing geo search with {geo_search}")

        # read wkt string from geo_search.roi_wkt_file into var
        with open(geo_search.roi_wkt_file, "r") as wkt_file:
            wkt_str = wkt_file.read().replace("\n", "")

        # validate wkt string using shapely
        # TODO

        # perform search
        # TODO split interval into montly intervals
        for interval in split_into_monthly_intervals(geo_search.start, geo_search.end):
            # Make sure eodag is used
            # TODO Implemnent a provider switch in config
            if True:
                dag = eodag.EODataAccessGateway()

                # Query ESA (provider=cop_dataspace)
                result = dag.search_all(
                    productType="S1_SAR_SLC",
                    start=interval[0].isoformat(),
                    end=interval[1].isoformat(),
                    geom=wkt_str,
                    provider="cop_dataspace",
                )

                # The eodag package does not allow us to search by relative
                # orbit, so we need to filter out the configured relative
                # orbits ourselves
                for orbit in geo_search.relative_orbits:
                    logger.info(f"Filtering relative orbit {orbit} from result")
                    orbit_products = result.crunch(
                        FilterProperty(dict(relativeOrbitNumber=orbit))
                    )

                    logger.info(f"Downloading results for orbit {orbit}")
                    download_eodag_products(download_config, orbit_products)
            else:
                result = asf.geo_search(
                    dataset=geo_search.dataset,
                    start=interval[0],
                    end=interval[1],
                    intersectsWith=wkt_str,
                    relativeOrbit=geo_search.relative_orbits,
                    processingLevel=geo_search.product_type,
                )

                product_count = len(result)
                logger.info(f"Found {str(product_count)} products")
                download_products(download_config, result)

    logger.info("Download done")


def download_eodag_products(download_config, result):
    """Download eodag result products.

    Parameters
    ----------
    download_config:
        download configuration
    result:
        query result

    """
    for product in result:
        download_eodag_product(download_config, product)


def download_products(download_config, result):
    """Download products from a result.

    Parameters
    ----------
    download_config:
        download configuration
    result:
        query result

    """
    for product in result:
        download_product(download_config, product)


def download_eodag_product(download_config, product):
    """Download eodag product.

    Parameters
    ----------
    download_config:
        download configuration
    product:
        the product to download

    TODO Test this. Check geojson functionality.
    """
    file_name = (
        str(product.properties["productIdentifier"].split("/").pop())[:-5] + ".zip"
    )
    relative_orbit = str(product.properties["relativeOrbitNumber"])
    orbit_direction = product.properties["orbitDirection"]
    polarization = product.properties["polarizationChannels"].replace("&", "+")

    target_directory = compose_product_download_path(
        base_directory=download_config.base_directory,
        file_name=file_name,
        relative_orbit=relative_orbit,
        orbit_direction=orbit_direction,
        polarization=polarization,
    )

    target_file = target_directory.joinpath(file_name)

    logger.debug(f"Target directory: {target_directory}")
    logger.debug(f"Target file: {target_file}")

    if os.path.isfile(target_file) and not download_config.force:
        logger.debug(
            f"Target file: {target_file} already exists. "
            "Force option not set. "
            "Skipping download"
        )
        return

    if os.path.isfile(target_file) and download_config.force:
        logger.debug(
            f"Target file: {target_file} already exists. "
            "Force option set. "
            f"Removing file: {target_file}"
        )
        if not download_config.dry_run:
            os.remove(target_file)

    logger.debug("Creating directories")
    if not download_config.dry_run:
        os.makedirs(target_directory, exist_ok=True)

    logger.info(f"Downloading {file_name}")
    if not download_config.dry_run:
        downloaded_product = product.download(
            output_dir=target_directory, extract=False, delete_archive=False
        )

        if download_config.verify:
            logger.warn("Checksum verificiation not possible with ESA provider.")

        # Construct a product geojson, since eodag only gives us the geometry property of the
        # full geojson
        product_geojson = {}
        product_geojson["type"] = "Feature"
        product_geojson["geometry"] = json.loads(shapely.to_geojson(product.geometry))
        product_geojson["properties"] = product.properties

        # Write out the geojson to a file
        logger.debug(f"target_file: '{target_file}'")
        product_geojson_file = str(target_file)[:-4] + ".json"
        logger.debug(f"product_geojson_file: '{product_geojson_file}'")
        logger.info("Saving product geojson to " f"{product_geojson_file}")
        with open(product_geojson_file, "w") as f:
            f.write(json.dumps(product_geojson, indent=2))


def download_product(download_config, product):
    """Download a product.

    Parameters
    ----------
    download_config:
        download configuration
    product:
        the product to download

    """
    target_directory = compose_product_download_path(
        base_directory=download_config.base_directory,
        file_name=product.properties["fileName"],
        relative_orbit=str(product.properties["pathNumber"]),
        orbit_direction=product.properties["flightDirection"],
        polarization=product.properties["polarization"],
    )

    target_file = target_directory.joinpath(product.properties["fileName"])

    logger.debug(f"Target directory: {target_directory}")
    logger.debug(f"Target file: {target_file}")

    if os.path.isfile(target_file) and not download_config.force:
        logger.debug(
            f"Target file: {target_file} already exists. "
            "Force option not set. "
            "Skipping download"
        )
        return

    if os.path.isfile(target_file) and download_config.force:
        logger.debug(
            f"Target file: {target_file} already exists. "
            "Force option set. "
            "Removing file: {target_file}"
        )
        if not download_config.dry_run:
            os.remove(target_file)

    logger.debug("Creating directories")
    if not download_config.dry_run:
        os.makedirs(target_directory, exist_ok=True)

    logger.info(f"Downloading {product.properties['fileName']}")
    if not download_config.dry_run:
        product.download(path=target_directory)

        if download_config.verify:
            logger.info("Verifying checksum")
            if verify_checksum(file=target_file, checksum=product.properties["md5sum"]):
                logger.info("Checksum OK")
            else:
                logger.error("Checksum FAILED")
                return

        product_geojson_file = str(target_file)[:-4] + ".json"
        logger.info("Saving product geojson to " f"{product_geojson_file}")
        f = open(product_geojson_file, "w")
        f.write(json.dumps(product.geojson(), indent=2))
        f.close()


def split_into_monthly_intervals(start_datetime, end_datetime):
    """Split interval into monthly intervals.

    Parameters
    ----------
    start_datetime: datetime
        start of the interval
    end_datetime: datetime
        end of the interval

    Returns
    -------
    list
        A list of intervals

    Notes
    -----
    Intervals are split on the end of the month, so even if the interval is
    smaller than one month but the interval includes the end of a month two
    intervals are returned.
    """
    logger.debug(
        f"Splitting interval {start_datetime} - {end_datetime} "
        "into monthly intervals"
    )
    logger.debug(f"Log level: {logger.level}")
    intervals = []
    current_start = start_datetime

    while current_start < end_datetime:
        # Calculate the start of the next month
        next_month_start = (current_start + relativedelta(months=1)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        # Calculate the end of the current interval (end of current month)
        current_end = min(next_month_start - timedelta(seconds=1), end_datetime)
        intervals.append((current_start, current_end))
        current_start = next_month_start

    logger.debug(f"Returning {len(intervals)} intervals")
    logger.debug(f"{intervals}")
    return intervals


def verify_checksum(file, checksum: str):
    """Verify checksum of a file.

    Parameters
    ----------
    file:
        The file to verify the checksum of
    checksum: str
        The checksum to compare against

    Returns
    -------
    bool
        True if checksum matches, False if it doesn't
    """
    # Log debugging info
    logger.debug("file: %s.", file)
    logger.debug("original checksum: %s.", checksum)

    # Open the file
    with open(file, "rb") as f:
        # Compute the checksum, chunking the checksum process so as
        # not to fill up memory
        computed_checksum = hashlib.md5()
        chunk = f.read(8192)
        while chunk:
            computed_checksum.update(chunk)
            chunk = f.read(8192)

    # Log debugging info
    logger.debug("computed checksum: %s.", computed_checksum.hexdigest())

    # Compare checksum provided as argument against checksum of file
    if checksum != computed_checksum.hexdigest():
        # Checksum does not match
        return False
    else:
        # Checksum matches
        return True
