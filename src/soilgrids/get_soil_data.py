"""
Module Name: get_soil_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: Februray, 2024
Description: Functions for downloading and processing selected soil data. 
"""

from copernicus import utils as ut_cop
import numpy as np
import requests
from pathlib import Path


def construct_data_file_name(folder, location, file_suffix):
    """
    Construct data file name.

    Args:
        folder (str or Path): Folder where the data file will be stored.
        location (str or dict): Location information ('DEIMS.iD' or {'lat': float, 'lon': float}).

    Returns:
        Path: Constructed data file name as a Path object.
    """
    # Get folder with path appropriate for different operating systems
    folder = Path(folder)

    if ut_cop.is_dict_of_2_floats(location) and set(location.keys()) == {
        "lat",
        "lon",
    }:  # location as dictionary with lat, lon
        formatted_lat = f"lat{location['lat']:.2f}".replace(".", "-")
        formatted_lon = f"lon{location['lon']:.2f}".replace(".", "-")
        file_name = folder / f"{formatted_lat}_{formatted_lon}_Soil{file_suffix}"
    elif isinstance(location, str):  # location as string (DEIMS.iD)
        file_name = folder / f"{location}__Soil{file_suffix}"
    else:
        raise ValueError("Unsupported location format.")

    return file_name


def shape_soildata_4_file(array):
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


def configure_soilgrids_request(coordinates):
    """
    Configure a request for SoilGrids API based on given coordinates.

    Parameters:
        coordinates (dict): Dictionary containing 'lon' and 'lat' keys representing the longitude and latitude.

    Returns:
        dict: Request configuration including URL and parameters.
    """
    return {
        "url": "https://rest.isric.org/soilgrids/v2.0/properties/query",
        "params": {
            "lon": coordinates["lon"],
            "lat": coordinates["lat"],
            "property": ["clay", "silt", "sand"],
            "depth": [
                "0-5cm",
                "0-30cm",
                "5-15cm",
                "15-30cm",
                "30-60cm",
                "60-100cm",
                "100-200cm",
            ],
            "value": ["Q0.05", "Q0.5", "Q0.95", "mean", "uncertainty"],
        },
    }

    # full options, Q0.5=median
    # "property": ["bdod", "cec", "cfvo", "clay", "nitrogen", "ocd", "ocs", "phh2o", "sand", "silt", "soc", "wv0010", "wv0033", "wv1500"],
    # "depth": ["0-5cm", "0-30cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"],
    # "value": ["Q0.05", "Q0.5", "Q0.95", "mean", "uncertainty"]


def download_soilgrids(request):
    """
    Download data from SoilGrids REST API.

    Parameters:
        request (dict): Dictionary containing the request URL (key: 'url') and parameters (key: 'params').

    Returns:
        dict: JSON response data.

    Raises:
        Exception: If the download fails, raises an exception with the error message and status code.
    """
    print(f"Soilgrids REST API download from {request["url"]}... ", end='')
    response = requests.get(request["url"], params=request["params"])

    if response.status_code == 200:
        print(f"completed.")

        return response.json()
    else:
        raise Exception("Soilgrids REST API download Error:", response.status_code)


# # some hihydrosoil tests, not working so far..
# def query_hihydrosoil_data(coordinates):
#     # Initialize the Earth Engine module
#     ee.Initialize()

#     # Define the image collection paths
#     ksat_collection_path = "projects/sat-io/open-datasets/HiHydroSoilv2_0/ksat"

#     # Load the image collections
#     ksat_collection = ee.ImageCollection(ksat_collection_path)

#     # Define a region of interest (e.g., a point)
#     point = ee.Geometry.Point(coordinates["lon"], coordinates["lat"])

#     # Get the image values at the point for a specific date
#     ksat_value = (
#         ksat_collection.filterBounds(point)
#         .first()
#         .reduceRegion(reducer=ee.Reducer.first(), geometry=point)
#     )

#     print(ksat_value.getInfo())

#     return ksat_value


def get_layer_data(soilgrids_data, reference_layers, value_type="mean"):
    """
    Extract layer data and units from Soilgrids data.

    Parameters:
        soilgrids_data (dict): Soilgrids data containing layer information.
        reference_layers (list): List of layer names to extract data and units for.
        value_type (str): Value to extract data for (default is "mean").

    Returns:
        tuple: Tuple containing layer data array and layer units array.
    """
    print(f"Reading from Soilgrids data...")

    # Initialize layer_data array with zeros, and layer_units with empty strings
    layer_data = np.zeros(
        (
            len(reference_layers),
            len(soilgrids_data["properties"]["layers"][0]["depths"]),
        ),
        dtype=float,
    )
    layer_units = [""] * len(reference_layers)

    # Iterate through reference_layers
    for l_index, layer_name in enumerate(reference_layers):
        # Find the corresponding layer in soilgrids_data
        for layer in soilgrids_data["properties"]["layers"]:
            if layer["name"] == layer_name:
                layer_units[l_index] = layer['unit_measure']['target_units']

                # Iterate through depths and fill the layer_data array
                for d_index, depth in enumerate(layer["depths"]):
                    layer_data[l_index, d_index] = (
                        depth["values"]["mean"] / layer["unit_measure"]["d_factor"]
                    )
                    print(
                        f"Depth {depth['label']}, {layer_name}",
                        f"mean: {layer_data[l_index, d_index]} {layer_units[l_index]}"
                    )
                break  # Stop searching once the correct layer is found

    return layer_data, layer_units


def map_depths_soilgrids_grassmind(layer_data, layer_names, layer_units):
    """
    Map data from Soilgrids depths to Grassmind depths.

    Parameters:
        layer_data (numpy.ndarray): Array containing layer data.
        layer_names (list): List of layer names.
        layer_units (list): List of layer units.

    Returns:
        numpy.ndarray: Array containing mapped mean values.
    """
    print(f"Mapping data from Soilgrids depths to Grassmind depths...")
    # Define number of new depths, 0-200cm in 10cm steps
    new_depths_number = 20  
    new_depths_step = 10

    # Define soilgrids depths' boundaries
    old_depths = np.array([[0, 5], [5, 15], [15, 30], [30, 60], [60, 100], [100, 200]])

    # Initialize array to store mapped mean values
    mapped_data = np.zeros((layer_data.shape[0], new_depths_number), dtype=float)

    # Iterate over each 10cm interval
    for d_new in range(new_depths_number):
        start_depth = d_new * new_depths_step
        end_depth = (d_new + 1) * new_depths_step

        # Find the indices of soilgrid depths within the new 10cm interval
        d_indices = np.where(
            (start_depth < old_depths[:, 1]) & (old_depths[:, 0] < end_depth)
        )[0]

        # For each layer, calculate the mean of old values (1 or 2 values) for the new 10cm interval
        mapped_data[:, d_new] = np.mean(layer_data[:, d_indices], axis=1)
        print(f"Depth {start_depth}-{end_depth}cm", end='')

        for l_index in range(len(layer_names)):
            print(f", {layer_names[l_index]}",
                  f"mean: {mapped_data[l_index, d_new]:.2f} {layer_units[l_index]}", end='')
        
        print("")

    return mapped_data


def get_layer_means(layer_data, layer_names, conversion_factor=1, conversion_units=None):
    """
    Calculate layer data means over all depths (equal weight for each depth).

    Parameters:
        layer_data (numpy.ndarray): Array containing layer data.
        layer_names (list): List of layer names.
        conversion_factor (float): Conversion factor to apply to the values (default is 1).
        conversion_units (list, optional): List of conversion units for each layer (default is 'None').

    Returns:
        numpy.ndarray: Array containing layer means.
    """
    print(f"Averaging data over all depths...")
    layer_means = np.mean(layer_data, axis=1) * conversion_factor

    if conversion_units is None:
        conversion_units = [""] * len(layer_names)

    for l_index in range(len(layer_names)):
        print(f"Depth 0-200cm, {layer_names[l_index]}",
              f"mean: {layer_means[l_index]:.4f} {conversion_units[l_index]}")

    return layer_means


def soil_data_2_txt_file(soilgrids_data, coordinates):
    # Reference layers (in Grassmind order) to assign values correctly
    reference_layers = ["silt", "clay", "sand"]

    layer_data_soilgrids, layer_units = get_layer_data(soilgrids_data, reference_layers, value_type="mean")
    layer_data_grassmind = map_depths_soilgrids_grassmind(layer_data_soilgrids, reference_layers, layer_units)

    # Mean over all layers for Grassmind input file, convert from % to proportions
    layer_data_total_means = get_layer_means(layer_data_grassmind, reference_layers, conversion_factor=1e-2)

    file_name = construct_data_file_name("soilDataPrepared", coordinates, ".txt")

    # Create data directory if missing
    Path(file_name).parent.mkdir(parents=True, exist_ok=True)

    # Write file to directory
    np.savetxt(
        file_name,
        shape_soildata_4_file(
            layer_data_total_means
        ),  # or: layer_data_grassmind for all depths
        delimiter="\t",
        fmt="%.4f",
        header="\t".join(list(map(str.capitalize, reference_layers))),
        comments="",
    )

    print(f"Text file with Soilgrids data prepared.")
