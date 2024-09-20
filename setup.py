from setuptools import setup

# Project metadata
name = "soilgrids"
version = "0.1.0"
author = "Thomas Banitz, Franziska Taubert, Tuomas Rossi, BioDT"
description = "Retrieve soil data from Soilgrids and HiHydroSoil, and prepare as grassland model input files"
url = "https://github.com/BioDT/general-soilgrids-soil-data"
license = "EUPL v1.2"

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
    python_requires=">=3.10",
    install_requires=install_requires,
)
