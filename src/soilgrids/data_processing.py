"""
Module Name: data_processing.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Building block for obtaining selected soil data at given location from 
SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil maps).
"""

from copernicus import utils as ut_cop
from soilgrids import get_soil_data as gsd


def data_processing(coordinates, deims_id):
    """
    Download data from Soilgrids. Convert to .txt files.

    Parameters:
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

    # SoilGrids composition part of the data
    composition_property_names = ["silt", "clay", "sand"]
    composition_request = gsd.configure_soilgrids_request(
        coordinates, composition_property_names
    )
    composition_raw = gsd.download_soilgrids(composition_request)
    composition_data = gsd.get_soilgrids_data(
        composition_raw, composition_property_names, value_type="mean"
    )

    # HiHydroSoil part of the data
    hihydrosoil_data = gsd.get_hihydrosoil_data(coordinates)

    # # SoilGrids nitrogen part of the data
    # nitrogen_property_names = ["nitrogen", "bdod"]
    # nitrogen_request = gsd.configure_soilgrids_request(
    #     coordinates, nitrogen_property_names
    # )
    # nitrogen_raw = gsd.download_soilgrids(nitrogen_request)
    # nitrogen_data = gsd.get_soilgrids_data(
    #     nitrogen_raw, nitrogen_property_names, value_type="mean"
    # )

    gsd.soil_data_to_txt_file(
        coordinates,
        composition_data,
        composition_property_names,
        hihydrosoil_data,
        # nitrogen_data,
    )
