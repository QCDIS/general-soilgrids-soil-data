"""
Module Name: data_processing.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: February, 2024
Description: Building block for obtaining selected soil data at given location from 
SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil maps).
"""

from soilgrids import utils as ut
from soilgrids import get_soil_data as gsd


def data_processing(coordinates, deims_id, file_name=None, hhs_local=False):
    """
    Download data from Soilgrids and HiHydroSoil maps. Convert to .txt files.

    Parameters:
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.
        deims_id (str): Identifier of the eLTER site.
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).
        hhs_local (bool): Look for HiHydroSoil maps as local files (default is False).
    """

    if coordinates is None:
        if deims_id:
            coordinates = ut.get_deims_coordinates(deims_id)
        else:
            raise ValueError(
                "No location defined. Please provide coordinates or DEIMS.iD!"
            )

    # SoilGrids composition part of the data
    composition_property_names = ["silt", "clay", "sand"]
    composition_request = gsd.configure_soilgrids_request(
        coordinates, composition_property_names
    )
    composition_raw, time_stamp = gsd.download_soilgrids(composition_request)
    data_query_protocol = [[composition_request["url"], time_stamp]]
    composition_data = gsd.get_soilgrids_data(
        composition_raw, composition_property_names
    )

    # HiHydroSoil part of the data
    hihydrosoil_data, hihydrosol_queries = gsd.get_hihydrosoil_data(
        coordinates, hhs_local
    )
    data_query_protocol.extend(hihydrosol_queries)

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
        data_query_protocol,
        file_name,
        # nitrogen_data,
    )
