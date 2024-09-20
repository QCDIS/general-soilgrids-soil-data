"""
Module Name: utils.py
Description: Utility functions for soilgrids building block.

Copyright (C) 2024
- Thomas Banitz, Franziska Taubert, Helmholtz Centre for Environmental Research GmbH - UFZ, Leipzig, Germany
- Tuomas Rossi, CSC – IT Center for Science Ltd., Espoo, Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl
"""

import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyproj
import rasterio
import requests


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


def extract_raster_value(tif_file, location, attempts=5, delay=2):
    """
    Extract value from raster file at specified coordinates.

    Parameters:
        tif_file (str): TIF file path or URL.
        location (dict): Dictionary with 'lat' and 'lon' keys.
        band_number (int): Band number for which the value shall be extracted (default is 1).
        attempts (int): Number of attempts to open the TIF file in case of errors (default is 5).
        delay (int): Number of seconds to wait between attempts (default is 2).

    Returns:
        tuple: Extracted value (None if extraction failed), and time stamp.
    """
    while attempts > 0:
        time_stamp = datetime.now(timezone.utc).isoformat()

        try:
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

            return value[0], time_stamp
        except rasterio.errors.RasterioError as e:
            attempts -= 1
            print(f"Reading TIF file failed (Error {e}).")

            if attempts > 0:
                print(f" Retrying in {delay} seconds ...")
                time.sleep(delay)
            else:
                return None, time_stamp


def check_url(url, attempts=3, delay=2):
    """
    Check if a file exists at the specified URL and retrieve its content type.

    Parameters:
        url (str): URL to check.
        attempts (int): Number of attempts in case of connection errors or specific status codes (default is 3).
        delay (int): Number of seconds to wait between attempts (default is 2).

    Returns:
        str: URL if existing (original or redirected), None otherwise.
    """
    if not url:
        return None

    retry_status_codes = {502, 503, 504}

    while attempts > 0:
        try:
            response = requests.head(url, allow_redirects=True)

            if response.status_code == 200:
                return response.url
            elif response.status_code in retry_status_codes:
                attempts -= 1

                if attempts > 0:
                    time.sleep(delay)
            else:
                return None
        except requests.ConnectionError:
            attempts -= 1

            if attempts > 0:
                time.sleep(delay)

    return None


def list_to_file(list_to_write, column_names, file_name):
    """
    Write a list of tuples to a text file (tab-separated) or csv file (;-separated) or an Excel file.

    Parameters:
        list_to_write (list): List of strings or tuples or dictionaries to be written to the file.
        column_names (list): List of column names (strings).
        file_name (str or Path): Path of the output file (suffix determines file type).
    """
    # Convert string entries to single item tuples
    list_to_write = [
        (entry,) if isinstance(entry, str) else entry for entry in list_to_write
    ]

    # Check if list_to_write contains dictionaries
    if isinstance(list_to_write[0], dict):
        # Convert dictionaries to lists of values based on column_names
        list_to_write = [
            [entry.get(col, "") for col in column_names] for entry in list_to_write
        ]
    # Check if all tuples in the list have the same length as the column_names list
    elif not all(len(entry) == len(column_names) for entry in list_to_write):
        print(
            f"Error: All tuples in the list must have {len(column_names)} entries (same as column_names)."
        )

        return

    file_path = Path(file_name)
    file_suffix = file_path.suffix.lower()

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    if file_suffix in [".txt", ".csv"]:
        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = (
                csv.writer(file, delimiter="\t")
                if file_suffix == ".txt"
                else csv.writer(file, delimiter=";")
            )
            header = column_names
            writer.writerow(header)  # Header row

            for entry in list_to_write:
                writer.writerow(entry)
    elif file_suffix == ".xlsx":
        df = pd.DataFrame(list_to_write, columns=column_names)
        df.to_excel(file_path, index=False)
    else:
        print(
            "Error: Unsupported file format. Supported formats are '.txt', '.csv' and '.xlsx'."
        )

    print(f"List written to file '{file_name}'.")
