# HOWTO

This document is a step by step guide to setting up and using CAROLINE Download to download Sentinel-1 data.


## Install CAROLINE Download

Install CAROLINE download using pip:

```
pip install git+https://github.com/TUDelftGeodesy/caroline-download.git@main
```


## Setup Authentication

### Register an account with NASA Earthdata

Downloading data from ASF requires an account with the NASA Earthdata Login system. You can register an account with their [user registration form](https://urs.earthdata.nasa.gov/users/new).

### Create a netrc file

In your home directory, create a .netrc file with the following content

```
machine urs.earthdata.nasa.gov
login <yourusername>
password <yourpassword>
```

!!! Note
    <ul>
    <li>Replace &lt;yourusername&gt; with to your username</li>
    <li>Replace &lt;yourpassword&gt; with to your password</li>
    </ul>

Make sure the .netrc is only readable for you:
```
chmod 700 .netrc
```

!!! Danger
    By not makeing sure your .netrc is readable just for you you are at risk of other people abusing your login credentials. Make sure to follow above instructions.

## Configure CAROLINE Download

Create a YAML file named `caroline-download.yml` with the following content:
```yaml
---
# caroline-download.yml

download:
  base_directory: "/path/to/base_directory"
```

## Create a ROI file

In a moment we'll be creating our query for downloading the data. The query is based on a region of interest. So first we store our ROI in a file in the Well-Known Text ([WKT](https://libgeos.org/specifications/wkt/)) format.

Create a file containing a valid WKT string e.g. a polygon representing the Bermuda Triangle.

Store the contents below in a file named `bermuda.wkt`:
```
POLYGON ((-64.8 32.3, -65.5 18.3, -80.3 25.2, -64.8 32.3))
```

## Create a query configuration

Now we are ready to create our query configuration. Create a YAML file with the name `bermuda.yml` with the following content:

```
---
# bermuda.yml

geo_search:
  dataset: "SENTINEL-1"
  start: "one month ago"
  end: "now"
  roi_wkt_file: "bermuda.wkt"
  relative_orbits: [77]
  product_type: "SLC"
```

## Start downloading

Finally time to start downloading some data!

```
caroline-download --config caroline-download.yml --geo-search bermuda.yml
```
