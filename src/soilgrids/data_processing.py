"""
Module Name: data_processing.py
Description: Building block for obtaining selected soil data at given location from
             SoilGrids and derived data sources (Soilgrids REST API, HiHydroSoil maps).

Copyright (C) 2024
- Thomas Banitz, Franziska Taubert, Helmholtz Centre for Environmental Research GmbH - UFZ, Leipzig, Germany
- Tuomas Rossi, CSC – IT Center for Science Ltd., Espoo, Finland

Licensed under the EUPL, Version 1.2 or - as soon they will be approved
by the European Commission - subsequent versions of the EUPL (the "Licence").
You may not use this work except in compliance with the Licence.

You may obtain a copy of the Licence at:
https://joinup.ec.europa.eu/software/page/eupl

This project has received funding from the European Union's Horizon Europe Research and Innovation
Programme under grant agreement No 101057437 (BioDT project, https://doi.org/10.3030/101057437).
The authors acknowledge the EuroHPC Joint Undertaking and CSC – IT Center for Science Ltd., Finland
for awarding this project access to the EuroHPC supercomputer LUMI, hosted by CSC – IT Center for
Science Ltd., Finlande and the LUMI consortium through a EuroHPC Development Access call.
"""

from soilgrids import get_soil_data as gsd


def data_processing(coordinates, *, file_name=None, hhs_cache=None):
    """
    Download data from Soilgrids and HiHydroSoil maps. Convert to .txt files.

    Parameters:
        coordinates (dict): Dictionary with 'lat' and 'lon' keys ({'lat': float, 'lon': float}).
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).
        hhs_cache (Path): Path for local HiHydroSoil map directory (optional).
    """

    if "lat" in coordinates and "lon" in coordinates:
        print(
            f"Preparing soil data for latitude: {coordinates['lat']}, longitude: {coordinates['lon']} ..."
        )
    else:
        raise ValueError(
            "Coordinates not correctly defined. Please provide as dictionary ({'lat': float, 'lon': float})!"
        )

    # SoilGrids composition part of the data
    composition_property_names = ["silt", "clay", "sand"]
    composition_request = gsd.configure_soilgrids_request(
        coordinates, composition_property_names
    )
    composition_raw, time_stamp = gsd.download_soilgrids(composition_request)
    data_query_protocol = [[composition_request["url"], time_stamp]]
    composition_data, composition_data_complete = gsd.get_soilgrids_data(
        composition_raw, composition_property_names
    )

    # HiHydroSoil part of the data
    hihydrosoil_data, hihydrosoil_data_complete, hihydrosoil_queries = (
        gsd.get_hihydrosoil_data(
            coordinates,
            cache=hhs_cache,
        )
    )
    data_complete = composition_data_complete and hihydrosoil_data_complete
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
        data_complete=data_complete,
        # nitrogen_data,
    )
