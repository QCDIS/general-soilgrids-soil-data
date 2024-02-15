from setuptools import setup
from pathlib import Path

# Project metadata
name = "soilgrids"
version = "0.1.0"
author = "Thomas Banitz, Franziska Taubert, BioDT"
description = "Retrieve soil data from Soilgrids and prepare as GRASSMIND input files"
url = "https://github.com/BioDT/general-soilgrids-soil-data"
license = "MIT"

# Specify project dependencies from a requirements.txt file
with open("requirements.txt", "r") as req_file:
    install_requires = req_file.readlines()

# Setup configurationpip
setup(
    name=name,
    version=version,
    author=author,
    description=description,
    url=url,
    license=license,
    entry_points={
        "console_scripts": [
            "soilgrids_data_processing = soilgrids.data_processing:main"
        ]
    },
    install_requires=install_requires,
)
