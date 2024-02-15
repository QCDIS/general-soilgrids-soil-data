"""
Module Name: get_soil_data.py
Author: Thomas Banitz, Tuomas Rossi, Franziska Taubert, BioDT
Date: Februray, 2024
Description: Functions for downloading and processing selected soil data. 
"""

# import json
import numpy as np
import requests


def configure_data_request(coordinates):
    request = {
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

    return request


def download_soil_data(request):
    response = requests.get(request["url"], params=request["params"])

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code)


def get_layer_means(soil_data, reference_layers):
    # Initialize layer_means array with zeros
    layer_means = np.zeros(
        (len(reference_layers), len(soil_data["properties"]["layers"][0]["depths"])),
        dtype=float,
    )

    # Iterate through reference_layers
    for l_index, layer_name in enumerate(reference_layers):
        # Find the corresponding layer in soil_data["properties"]["layers"]
        for layer in soil_data["properties"]["layers"]:
            if layer["name"] == layer_name:
                # Iterate through depths and fill the layer_means array
                for d_index, depth in enumerate(layer["depths"]):
                    mean_converted = (
                        depth["values"]["mean"] / layer["unit_measure"]["d_factor"]
                    )
                    layer_means[l_index, d_index] = mean_converted
                    print(
                        f"Depth {depth['label']}, {layer_name} mean: {mean_converted} {layer['unit_measure']['target_units']}"
                    )
                break  # Stop searching once the correct layer is found

    return layer_means


# ToDo: check here, switch loops?
def map_depths_soilgrids_grassmind(layer_means):
    # Define depth labels for 10cm intervals
    new_depth_labels = [
        "0-10cm",
        "10-20cm",
        "20-30cm",
        "30-40cm",
        "40-50cm",
        "50-60cm",
        "60-70cm",
        "70-80cm",
        "80-90cm",
        "90-100cm",
        "100-110cm",
        "110-120cm",
        "120-130cm",
        "130-140cm",
        "140-150cm",
        "150-160cm",
        "160-170cm",
        "170-180cm",
        "180-190cm",
        "190-200cm",
    ]

    # Initialize array to store mapped mean values
    mapped_means = np.zeros((layer_means.shape[0], len(new_depth_labels)), dtype=float)

    # Iterate over each layer
    for i in range(layer_means.shape[0]):
        # Iterate over each 10cm interval
        for j in range(len(new_depth_labels)):
            # Calculate the mean value for the corresponding 10cm interval
            start_depth = j * 10
            end_depth = (j + 1) * 10
            mean_value = np.mean(
                layer_means[i][
                    (start_depth < layer_means[i]) & (layer_means[i] <= end_depth)
                ]
            )
            mapped_means[i, j] = mean_value

    return mapped_means


def soil_data_2_txt_file(soil_data):
    # Reference layers (in Grassmind order) to assign values correctly
    reference_layers = ["silt", "clay", "sand"]

    layer_means_depths_soilgrids = get_layer_means(soil_data, reference_layers)
    layer_means_depths_grassmind = map_depths_soilgrids_grassmind(
        layer_means_depths_soilgrids
    )

    print(" hold")

    # # Initialize layer_means array with zeros
    # layer_means = np.zeros(
    #     (len(reference_layers), len(soil_data["properties"]["layers"][0]["depths"])),
    #     dtype=float,
    # )

    # # Iterate through reference_layers
    # for l_index, layer_name in enumerate(reference_layers):
    #     # Find the corresponding layer in soil_data["properties"]["layers"]
    #     for layer in soil_data["properties"]["layers"]:
    #         if layer["name"] == layer_name:
    #             # Iterate through depths and fill the layer_means array
    #             for d_index, depth in enumerate(layer["depths"]):
    #                 mean_converted = (
    #                     depth["values"]["mean"] / layer["unit_measure"]["d_factor"]
    #                 )
    #                 layer_means[l_index, d_index] = mean_converted
    #                 print(
    #                     f"Depth {depth['label']}, {layer_name} mean: {mean_converted} {layer['unit_measure']['target_units']}"
    #                 )
    #             break  # Stop searching once the correct layer is found
