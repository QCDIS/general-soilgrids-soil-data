"""
Module Name: data_processing.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Building block for obtaining selected soil data at given location from 
SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil map).
"""

from soilgrids import get_soil_data as gsd
from soilgrids import utils as ut


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
            coordinates = ut.get_deims_coordinates(deims_id)
        else:
            raise ValueError(
                "No location defined. Please provide coordinates or DEIMS.iD!"
            )

    data_request = gsd.configure_data_request(coordinates)
    soil_data = gsd.download_soil_data(data_request)
    gsd.soil_data_2_txt_file(soil_data)

    print("g")

    # gsd.soil_data_2_txt_file(
    #     data_sets,
    #     data_var_specs,
    #     data_format,
    #     data_resolution,
    #     final_resolution,
    #     deims_id,
    #     coordinates,
    # )
