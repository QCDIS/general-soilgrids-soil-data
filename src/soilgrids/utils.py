"""
Module Name: utils.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Utility functions for soilgrids building block. 
"""

import deims


def get_deims_coordinates(deims_id):
    """
    Get coordinates for a DEIMS.iD.

    Args:
        deims_id (str): DEIMS.iD.

    Returns:
        dict: Coordinates as a dictionary with 'lat' and 'lon'.
    """
    deims_gdf = deims.getSiteCoordinates(deims_id, filename=None)
    # deims_gdf = deims.getSiteBoundaries(deims_id, filename=None)  # option: collect all coordinates from deims_gdf.boundary[0] ...
    lon = deims_gdf.geometry[0].x
    lat = deims_gdf.geometry[0].y
    print(f"Coordinates for DEIMS.id '{deims_id}' found.")
    print(f"Latitude: {lat}, Longitude: {lon}")
    return {"lat": lat, "lon": lon}
