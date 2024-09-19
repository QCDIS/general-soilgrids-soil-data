"""
Module Name: get_soil_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: Februray, 2024
Description: Functions for downloading and processing selected soil data, from sources:

             SoilGrids (https://soilgrids.org/)
             access via API (https://rest.isric.org/soilgrids/v2.0/docs)

             HiHydroSoil v2.0 (https://www.futurewater.eu/projects/hihydrosoil/)
             access via TIF Maps, provided upon request to FutureWater
"""

from datetime import datetime, timezone
import numpy as np
import requests
from pathlib import Path
from soilgrids import utils as ut
import time


def construct_soil_data_file_name(folder, location, file_suffix):
    """
    Construct data file name.

    Parameters:
        folder (str or Path): Folder where the data file will be stored.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).
        file_suffix (str): File suffix (e.g. '.txt').

    Returns:
        Path: Constructed data file name as a Path object.
    """
    # Get folder with path appropriate for different operating systems
    folder = Path(folder)

    if ("lat" in location) and (
        "lon" in location
    ):  # location as dictionary with lat, lon
        formatted_lat = f'lat{location["lat"]:.6f}'
        formatted_lon = f"lon{location['lon']:.6f}"
        file_start = f"{formatted_lat}_{formatted_lon}"
    elif "deims_id" in location:  # DEIMS.iD
        file_start = location["deims_id"]
    elif isinstance(location, str):  # location as string (DEIMS.iD)
        file_start = location
    else:
        raise ValueError("Unsupported location format.")

    file_name = folder / f"{file_start}__2020__soil{file_suffix}"

    return file_name


def shape_soildata_for_file(array):
    """
    Reshape a 1D array to 2D or transpose a 2D array.

    Parameters:
        array (numpy.ndarray): Input array.

    Returns:
        numpy.ndarray: Reshaped or transposed array.

    Raises:
        ValueError: If the input array is not 1D or 2D.
    """
    if array.ndim == 1:
        return array.reshape(1, -1)
    elif array.ndim == 2:
        return np.transpose(array)
    else:
        raise ValueError("Input array must be 1D or 2D.")


def configure_soilgrids_request(coordinates, property_names):
    """
    Configure a request for SoilGrids API based on given coordinates and properties.

    Parameters:
        coordinates (dict): Dictionary containing 'lon' and 'lat' keys.
        property_names (list): List of properties to download.

    Returns:
        dict: Request configuration including URL and parameters.
    """
    return {
        "url": "https://rest.isric.org/soilgrids/v2.0/properties/query",
        "params": {
            "lon": coordinates["lon"],
            "lat": coordinates["lat"],
            "property": property_names,
            "depth": [
                "0-5cm",
                "5-15cm",
                "15-30cm",
                "30-60cm",
                "60-100cm",
                "100-200cm",
            ],
            "value": ["mean"],
        },
    }

    # full options, Q0.5=median
    # "property": ["bdod", "cec", "cfvo", "clay", "nitrogen", "ocd", "ocs", "phh2o", "sand", "silt", "soc", "wv0010", "wv0033", "wv1500"],
    # "depth": ["0-5cm", "0-30cm" ????, "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"],
    # "value": ["Q0.05", "Q0.5", "Q0.95", "mean", "uncertainty"]


def download_soilgrids(request, attempts=6, delay_exponential=8, delay_linear=2):
    """
    Download data from SoilGrids REST API with retry functionality.

    Parameters:
        request (dict): Dictionary containing the request URL (key: 'url') and parameters (key: 'params').
        attempts (int): Total number of attempts (including the initial try). Default is 6.
        delay_exponential (int): Initial delay in seconds for request rate limit errors (default is 8).
        delay_linear (int): Delay in seconds for gateway errors and other failed requests (default is 2).

    Returns:
        tuple: JSON response data (dict) and time stamp.

    Raises:
        Exception: If the download fails after all attempts, raises an exception with the error message and status code.
    """
    print(f"Soilgrids REST API download from {request['url']} ... ")
    status_codes_rate = {429}  # codes for retry with exponentially increasing delay
    status_codes_gateway = {502, 503, 504}  # codes for retry with fixed time delay

    while attempts > 0:
        attempts -= 1
        time_stamp = datetime.now(timezone.utc).isoformat()

        try:
            response = requests.get(request["url"], params=request["params"])

            if response.status_code == 200:
                return response.json(), time_stamp
            elif response.status_code in status_codes_rate:
                print(f"Request rate limited (Error {response.status_code}).")

                if attempts > 0:
                    print(f"Retrying in {delay_exponential} seconds ...")
                    time.sleep(delay_exponential)
                    delay_exponential *= 2
            elif response.status_code in status_codes_gateway:
                print(f"Request failed (Error {response.status_code}).")

                if attempts > 0:
                    print(f"Retrying in {delay_linear} seconds ...")
                    time.sleep(delay_linear)
            else:
                raise Exception(
                    f"Soilgrids REST API download error: {response.reason} ({response.status_code})."
                )
        except requests.RequestException as e:
            print(f"Request failed {e}.")

            if attempts > 0:
                print(f"Retrying in {delay_linear} seconds ...")
                time.sleep(delay_linear)

    # After exhausting all attempts
    raise Exception("Maximum number of attempts reached. Failed to download data.")


def get_soilgrids_data(soilgrids_data, property_names):
    """
    Extract property data and units from Soilgrids data.

    Parameters:
        soilgrids_data (dict): Soilgrids data containing property information.
        property_names (list): List of properties to extract data and units for.

    Returns:
        numpy.ndarray: 2D array containing property data for various soil properties and depths (nan if no data found).
    """
    print("Reading Soilgrids data ...")

    # Initialize property_data array with zeros
    property_data = np.full(
        (
            len(property_names),
            len(soilgrids_data["properties"]["layers"][0]["depths"]),
        ),
        np.nan,
        dtype=float,
    )

    # Iterate through property_names
    for p_index, p_name in enumerate(property_names):
        # Find the corresponding property in soilgrids_data
        for prop in soilgrids_data["properties"]["layers"]:
            if prop["name"] == p_name:
                p_units = prop["unit_measure"]["target_units"]

                # Iterate through depths and fill the property_data array
                for d_index, depth in enumerate(prop["depths"]):
                    property_data[p_index, d_index] = (
                        (depth["values"]["mean"] / prop["unit_measure"]["d_factor"])
                        if depth["values"]["mean"] is not None
                        else None
                    )
                    print(
                        f"Depth {depth['label']}, {p_name}",
                        f"mean: {property_data[p_index, d_index]} {p_units}",
                    )
                break  # Stop searching once the correct property is found

    return property_data


def get_hihydrosoil_specs():
    """
    Create a dictionary of HiHydroSoil variable specifications.

    Each variable is identified by its name and includes the following information:
        hhs_name: HiHydroSoil variable name.
        hhs_unit: HiHydroSoil unit.
        map_to_float: Conversion factor from HiHydroSoil integer map value to actual float number.
        hhs_to_gmd: Conversion factor from HiHydroSoil unit to Grassmind unit.
        gmd_unit: Grassmind unit.
        gmd_name: Grassmind variable name, as used in final soil data file.

    Returns:
        dict: Dictionary of variable specifications, where each key is a variable name,
              and each value is a dictionary of specifications.

    """
    hihydrosoil_specs = {
        "field capacity": {
            "hhs_name": "WCpF2",
            "hhs_unit": "m³/m³",
            "map_to_float": 1e-4,
            "hhs_to_gmd": 1e2,  # to %
            "gmd_unit": "V%",
            "gmd_name": "FC[V%]",
        },
        "permanent wilting point": {
            "hhs_name": "WCpF4.2",
            "hhs_unit": "m³/m³",
            "map_to_float": 1e-4,
            "hhs_to_gmd": 1e2,  # to %
            "gmd_unit": "V%",
            "gmd_name": "PWP[V%]",
        },
        "soil porosity": {
            "hhs_name": "WCsat",
            "hhs_unit": "m³/m³",
            "map_to_float": 1e-4,
            "hhs_to_gmd": 1e2,  # to %
            "gmd_unit": "V%",
            "gmd_name": "POR[V%]",
        },
        "saturated hydraulic conductivity": {
            "hhs_name": "Ksat",
            "hhs_unit": "cm/d",
            "map_to_float": 1e-4,
            "hhs_to_gmd": 1e1,  # cm to mm
            "gmd_unit": "mm/d",
            "gmd_name": "KS[mm/d]",
        },
    }

    return hihydrosoil_specs


def get_hihydrosoil_map_file(property_name, depth, map_local=False):
    """
    Generate file path or URL for a HiHydroSoil map based on the provided property name and depth.

    Parameters:
        property_name (str): Name of the soil property (e.g. "WCpF4.2" or "Ksat").
        depth (str): Depth layer (one of "0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm").
        map_local (bool): Look for map as local file (default is False).

    Returns:
        pathlib.Path or URL: File path or URL to the HiHydroSoil map.
    """
    file_name = property_name + "_" + depth + "_M_250m.tif"

    if map_local:
        map_file = ut.get_package_root() / "soilMapsHiHydroSoil" / file_name
        # map_file = Path(r"c:/_D/biodt_data/") / "soilMapsHiHydroSoil" / file_name

        if map_file.is_file():
            return map_file
        else:
            print(f"Error: Local file '{map_file}' not found!")
            print("Trying to access via URL ...")

    map_file = "http://opendap.biodt.eu/grasslands-pdt/soilMapsHiHydroSoil/" + file_name

    if ut.check_url(map_file):
        return map_file
    else:
        print(f"Error: File '{map_file}' not found!")

        return None


def get_hihydrosoil_data(coordinates, map_local):
    """
    Read HiHydroSoil data for the given coordinates and return as array.

    Parameters:
        coordinates (tuple): Coordinates ('lat', 'lon') to extract HiHydroSoil data from.
        map_local (bool): Look for map as local file instead of URL.

    Returns:
        tuple: Property data for various soil properties and depths (2D numpy.ndarray, nan if no data found), and list of query sources and time stamps.
    """
    print("Reading HiHydroSoil data ...")
    hhs_properties = get_hihydrosoil_specs()
    hhs_depths = ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"]

    # Initialize property_data array with zeros
    property_data = np.full(
        (len(hhs_properties), len(hhs_depths)),
        np.nan,
        dtype=float,
    )

    # Extract values from tif maps for each property and depth
    query_protocol = []

    for p_index, (p_name, p_specs) in enumerate(hhs_properties.items()):
        for d_index, depth in enumerate(hhs_depths):
            map_file = get_hihydrosoil_map_file(p_specs["hhs_name"], depth, map_local)

            if map_file:
                # Extract and convert value
                print(f"Reading from file '{map_file}' ...")
                value, time_stamp = ut.extract_raster_value(map_file, coordinates)
                query_protocol.append([map_file, time_stamp])

                if value != -9999:
                    property_data[p_index, d_index] = value * p_specs["map_to_float"]

            print(
                f"Depth {depth}, {p_name}"
                f": {property_data[p_index, d_index]:.4f} {p_specs['hhs_unit']}"
            )

    return property_data, query_protocol


def map_depths_soilgrids_grassmind(
    property_data, property_names, conversion_factor=1, conversion_units=None
):
    """
    Map data from Soilgrids depths to Grassmind depths.

    Parameters:
        property_data (numpy.ndarray): Array containing property data.
        property_names (list): List of property names.
        conversion_factor (float or array): Conversion factors to apply to the values (default is 1).
        conversion_units (list, optional): List of units after conversion for each property (default is 'None').

    Returns:
        numpy.ndarray: Array containing mapped property values.
    """
    print("Mapping data from Soilgrids depths to Grassmind depths ...")

    # Define number of new depths, 0-200cm in 10cm steps
    new_depths_number = 20
    new_depths_step = 10

    # Define SoilGrids depths boundaries
    old_depths = np.array([[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]])

    # Prepare conversion factors and units
    if isinstance(conversion_factor, float):
        conversion_factor = np.full((len(property_names),), conversion_factor)
    else:
        conversion_factor = np.array(conversion_factor)

    if conversion_units is None:
        conversion_units = [""] * len(property_names)

    # Initialize array to store mapped mean values
    if property_data.ndim == 1:
        data_to_map = property_data.copy().reshape(1, -1)
    else:
        data_to_map = property_data

    mapped_data = np.zeros((data_to_map.shape[0], new_depths_number), dtype=float)

    # Iterate over each 10cm interval
    for d_new in range(new_depths_number):
        start_depth = d_new * new_depths_step
        end_depth = (d_new + 1) * new_depths_step

        # Find the indices of SoilGrid depths within the new 10cm interval
        d_indices = np.where(
            (start_depth < old_depths[:, 1]) & (old_depths[:, 0] < end_depth)
        )[0]

        # For each property, calculate the mean of old values (1 or 2 values) for the new 10cm interval
        mapped_data[:, d_new] = (
            np.mean(data_to_map[:, d_indices], axis=1) * conversion_factor
        )
        print(f"Depth {start_depth}-{end_depth}cm", end="")

        for p_index in range(len(property_names)):
            print(
                f", {property_names[p_index]}"
                f": {mapped_data[p_index, d_new]:.4f} {conversion_units[p_index]}",
                end="",
            )

        print("")

    return mapped_data


def get_property_means(property_data, property_names, property_units=None):
    """
    Calculate property data means over all depths (equal weight for each depth).

    Parameters:
        property_data (numpy.ndarray): Array containing property data.
        property_names (list): List of property names.
        property_units (list, optional): List of units for each property (default is 'None').

    Returns:
        numpy.ndarray: Array containing property means.
    """
    print("Averaging data over all depths ...")
    property_means = np.mean(property_data, axis=1)

    if property_units is None:
        property_units = [""] * len(property_names)

    for p_index in range(len(property_names)):
        print(
            f"Depth 0-200cm, {property_names[p_index]}",
            f"mean: {property_means[p_index]:.4f} {property_units[p_index]}",
        )

    return property_means


def soil_data_to_txt_file(
    coordinates,
    composition_data,
    composition_property_names,
    hihydrosoil_data,
    data_query_protocol,
    file_name=None,
    # nitrogen_data,
):
    """
    Write SoilGrids and HiHydroSoil data to soil data TXT file in Grassmind format.

    Parameters:
        coordinates (tuple): Coordinates ('lat' and 'lon') for the data.
        composition_data (numpy.ndarray): SoilGrids data array.
        composition_property_names (list): Names of SoilGrids properties.
        hihydrosoil_data (numpy.ndarray): HiHydroSoil data array.
        data_query_protocol (list): List of sources and time stamps from retrieving soil data.
        file_name (str or Path): File name to save soil data (default is None, default file name is used if not provided).

    Returns:
        None
    """
    # Prepare SoilGrids composition data in Grassmind format
    composition_to_gmd = 1e-2  # % to proportions for all composition values
    composition_data_gmd = map_depths_soilgrids_grassmind(
        composition_data, composition_property_names, composition_to_gmd
    )

    # Mean over all depths
    composition_data_mean = get_property_means(
        composition_data_gmd, composition_property_names
    )

    # Prepare HiHydroSoil data in Grassmind format
    hhs_properties = get_hihydrosoil_specs()
    hhs_property_names = list(hhs_properties.keys())
    hhs_conversion_factor = [specs["hhs_to_gmd"] for specs in hhs_properties.values()]
    hhs_units_gmd = [specs["gmd_unit"] for specs in hhs_properties.values()]
    hhs_data_gmd = map_depths_soilgrids_grassmind(
        hihydrosoil_data, hhs_property_names, hhs_conversion_factor, hhs_units_gmd
    )

    # # Prepare SoilGrids nitrogen data in Grassmind format
    # # Not only mineral nitrogen!!
    # # Sum of total nitrogen (ammonia, organic and reduced nitrogen)
    # # as measured by Kjeldahl digestion plus nitrate–nitrite

    # # difficult to assess mineral N
    # # small fraction fo total N? general relation?
    # nitrogen_per_volume = nitrogen_data[0, :] * nitrogen_data[1, :]  # unit: g/dm³ (from: g/kg * kg/dm³)
    # nitrogen_to_gmd = 1e2 # 10cm depth layers mean 100 dm³ per m²
    # nitrogen_data_gmd = map_depths_soilgrids_grassmind(
    #     nitrogen_per_volume, ["total nitrogen"], nitrogen_to_gmd, ["g/m²"]
    # )
    # print("Warning: Total nitrogen data not used! Using default mineral nitrogen value for all depths: 1 g/m².")

    # Write collected soil data to TXT file
    if not file_name:
        file_name = construct_soil_data_file_name(
            "soilDataPrepared", coordinates, ".txt"
        )

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    # Soilgrids composition part
    composition_data_to_write = shape_soildata_for_file(
        composition_data_mean
    )  # all depths below
    composition_header = "\t".join(
        list(map(str.capitalize, composition_property_names))
    )
    np.savetxt(
        file_name,
        composition_data_to_write,
        delimiter="\t",
        fmt="%.4f",
        header=composition_header,
        comments="",
    )

    # HiHydroSoil part
    hhs_data_to_write = shape_soildata_for_file(hhs_data_gmd)
    gmd_depth_count = np.arange(1, 21).reshape(-1, 1)
    # gmd_rwc = np.ones((20, 1))
    # gmd_minn = np.ones((20, 1))
    hhs_data_to_write = np.concatenate(
        (
            gmd_depth_count,
            # gmd_rwc,
            hhs_data_to_write[:, :2],
            # gmd_minn,
            hhs_data_to_write[:, 2:4],
        ),
        axis=1,
    )
    gmd_names = [specs["gmd_name"] for specs in hhs_properties.values()]
    hhs_header = "\t".join(map(str, ["Layer"] + gmd_names))

    with open(file_name, "a") as f:  # Open file in append mode
        f.write("\n")  # Write an empty line
        np.savetxt(
            f,  # Use the file handle
            hhs_data_to_write,
            delimiter="\t",
            fmt="%.4f",
            header=hhs_header,
            comments="",
        )

    # # Soilgrids composition part for all depths, only for information
    # composition_data_to_write = shape_soildata_for_file(composition_data_gmd)
    # composition_data_to_write = np.concatenate(
    #     (gmd_depth_count, composition_data_to_write), axis=1
    # )
    # composition_header = "Layer\t" + composition_header

    # with open(file_name, "a") as f:  # Open file in append mode
    #     f.write("\n")  # Write an empty line
    #     np.savetxt(
    #         f,  # Use the file handle
    #         composition_data_to_write,
    #         delimiter="\t",
    #         fmt="%.4f",
    #         header=composition_header,
    #         comments="",
    #     )

    print(
        f"Processed soil data from Soilgrids and HiHydroSoil written to file '{file_name}'."
    )

    if data_query_protocol:
        file_name = file_name.with_name(
            file_name.stem + "__data_query_protocol" + file_name.suffix
        )
        ut.list_to_file(
            data_query_protocol,
            ["soil_data_source", "time_stamp"],
            file_name,
        )
