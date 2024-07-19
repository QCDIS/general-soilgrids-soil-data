"""
Module Name: utils.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Utility functions for soilgrids building block. 
"""

from pathlib import Path
import pyproj
import rasterio
import requests


def get_package_root():
    """
    Get the root directory of the package containing the current module.

    Returns:
        Path: The path to the package root directory.
    """
    # Get the file path of the current module
    module_path = Path(__file__).resolve()

    # Navigate up from the module directory until the package root is found
    for parent in module_path.parents:
        if (parent / "setup.py").is_file():
            return parent

    raise FileNotFoundError("Could not find package root.")


def reproject_coordinates(lat, lon, target_crs):
    """
    Reproject latitude and longitude coordinates to a target CRS.

    Parameters:
        lat (float): Latitude.
        lon (float): Longitude.
        target_crs (str): Target Coordinate Reference System in WKT format.

    Returns:
        tuple (float): Reprojected coordinates (easting, northing).
    """
    # Define the source CRS (EPSG:4326 - WGS 84, commonly used for lat/lon)
    src_crs = pyproj.CRS("EPSG:4326")

    # Create a transformer to convert from the source CRS to the target CRS
    # (always_xy: use lon/lat for source CRS and east/north for target CRS)
    transformer = pyproj.Transformer.from_crs(src_crs, target_crs, always_xy=True)

    # Reproject the coordinates (order is lon, lat!)
    east, north = transformer.transform(lon, lat)

    return east, north


def extract_raster_value(tif_file, location):
    """
    Extract values from raster file at specified coordinates.

    Parameters:
        tif_file (str): Path to TIF file.
        category_mapping (dict): Mapping of category indices to category names.
        location (dict): Dictionary with 'lat' and 'lon' keys.

    Returns:
        list: A list of extracted values.
    """
    with rasterio.open(tif_file) as src:
        # Get the target CRS (as str in WKT format) from the TIF file
        target_crs = src.crs.to_wkt()
        # (HiHydroSoil seems to work with lat/lon too, but better to keep transformation in.)

        # Reproject the coordinates to the target CRS
        east, north = reproject_coordinates(
            location["lat"], location["lon"], target_crs
        )

        # Extract the value at the specified coordinates
        value = next(src.sample([(east, north)]))

    return value[0]


def check_url(url):
    """
    Check if a file exists at the specified URL and retrieve its content type.

    Parameters:
        url (str): URL to check.

    Returns:
        str: URL if existing (original or redirected), None otherwise.
    """
    if url:
        try:
            response = requests.head(url, allow_redirects=True)  # Allow redirection

            if response.status_code == 200:
                return url  # response.url caused problems with HiHydroSoil file opening, but original url works
                # could be returned: content_type = response.headers.get("content-type")
            else:
                return None
        except requests.ConnectionError:
            return None
    else:
        return None
