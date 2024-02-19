"""
Module Name: data_processing.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Building block for obtaining selected soil data at given location from 
SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil maps).
"""

from copernicus import utils as ut_cop
from soilgrids import get_soil_data as gsd


def data_processing(
    coordinates,
    deims_id,
):
    """
    Download data from Soilgrids. Convert to .txt files.

    Args:
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.
        deims_id (str): Identifier of the eLTER site.
    """

    if coordinates is None:
        if deims_id:
            coordinates = ut_cop.get_deims_coordinates(deims_id)
        else:
            raise ValueError(
                "No location defined. Please provide coordinates or DEIMS.iD!"
            )

    # test hihydrosoil
    # hihydrosoil_data = gsd.query_hihydrosoil_data(coordinates)

    soilgrids_request = gsd.configure_soilgrids_request(coordinates)
    soilgrids_data = gsd.download_soilgrids(soilgrids_request)
    gsd.soil_data_2_txt_file(soilgrids_data, coordinates)
