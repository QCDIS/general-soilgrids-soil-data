"""
Module Name: data_processing.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: September, 2024
Description: Building block for obtaining selected soil data at given location from
SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil maps).
"""

from soilgrids import get_soil_data as gsd


def data_processing(coordinates, file_name=None, hhs_local=False):
    """
    Download data from Soilgrids and HiHydroSoil maps. Convert to .txt files.

    Parameters:
        coordinates (list of dict): List of dictionaries with "lat" and "lon" keys.
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).
        hhs_cache (Path): Path for local HiHydroSoil map directory (optional).
    """

    if coordinates is None:
        raise ValueError("No location defined. Please provide coordinates!")

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
    hihydrosoil_data, hihydrosoil_queries = gsd.get_hihydrosoil_data(
        coordinates,
        cache=hhs_cache,
    )
    data_query_protocol.extend(hihydrosoil_queries)

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
