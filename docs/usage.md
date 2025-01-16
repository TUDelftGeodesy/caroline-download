# User documentation

## Built in help

The builtin help illustrates basic usage:
```
caroline-download --help
usage: caroline-download [-h] [--config CONFIG] [--geo-search GEO_SEARCH] [--product-search PRODUCT_SEARCH]
                         [--force] [--verify] [--dry-run] [--log-file LOG_FILE] [--log-level LOG_LEVEL] [--quiet]

Download data for processing with CAROLINE Currently only downloads SENTINEL-1 SLC products from ASF (Alaska
Satellite Facility) with authentication using .netrc

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG       configuration file to use
  --geo-search GEO_SEARCH
                        download based on geo search
  --product-search PRODUCT_SEARCH
                        download a single product
  --force               force downloading, even if a product already exists locally
  --verify              verify checksum after downloading
  --dry-run             perform dry run. do not actually download anything
  --log-file LOG_FILE   log to LOG_FILE
  --log-level LOG_LEVEL
                        set log level
  --quiet               do not log anything to stderr

```

## Configuration

### Download configuration

The CLI requires basic configuration pertaining to the download process.

By default it looks for a configfile in 
```
CAROLINE_DOWNLOAD_CONFIG_DIR/caroline-download.yml
```

where CAROLINE_DOWNLOAD_CONFIG_DIR is an environment variable.

Alternatively, a configfile may be specified on the command line with the '--config' option.

This config file has the folllowing syntax:
```
---
# caroline-download.yml

download:
  base_directory: "/path/to/base_directory"
  force: False
  dry_run: False
```

`base_directory`

: Required. Top level directory where downloads are stored.

`force`

: Optional. Overwrite files if they exist.

`dry_run`

: Optional. Perform a dry run.


### Search configuration

To be able to download anything you have to specify what you want to download. This is done with a search specification

## Geo search

With the `--geo-search` option you specify a search specification based on a region of interest in a YAML file. 

The YAML file has the following syntax:
```yaml
---
# netherlands.yaml

geo_search:
  dataset: "SENTINEL-1"
  start: "one month ago"
  end: "now"
  roi_wkt_file: "netherlands.wkt"
  relative_orbits: [15, 37, 88, 110, 139, 161]
  product_type: "SLC"

```

`dataset`: 

: The required dataset e.g. SENTINEL-1
`start`: 

: The desired start time of the observation e.g. "one month ago"
`end`: 

: The desired end time of the observation e.g. "now"

`roi_wkt_file`: 

: Path to a file containing the ROI in wkt format.

`relative_orbits`: [15, 37, 88, 110, 139, 161]

: The desired relative orbits or tracks within the ROI.

`product_type`: 

: The desired product type. E.g. "SLC".

### Authentication

Authentication for downloading is currently done with a [netrc file](https://www.gnu.org/software/inetutils/manual/html_node/The-_002enetrc-file.html)

