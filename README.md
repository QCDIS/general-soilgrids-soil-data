# general-soilgrids-soil-data
Building block for obtaining selected soil data at given location from data sources:

    SoilGrids (https://soilgrids.org/)
    - Poggio L., Sousa L.M., Batjes N.H., Heuvelink G.B., Kempen B., Ribeiro E., Rossiter D. (2021):
      SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty.
      SOIL 7: 217‑240. https://doi.org/10.5194/soil-7-217-2021
    - access via API (https://rest.isric.org/soilgrids/v2.0/docs)

    HiHydroSoil v2.0 (https://www.futurewater.eu/projects/hihydrosoil/)
    - Simons, G.W.H., R. Koster, P. Droogers. (2020):
      HiHydroSoil v2.0 - A high resolution soil map of global hydraulic properties.
      FutureWater Report 213.
    - access via TIF Maps, provided upon request to FutureWater
    - redistributed with permission and without changes at:
      http://opendap.biodt.eu/grasslands-pdt/soilMapsHiHydroSoil/

Usage:
   Call "data_processing(coordinates, *, file_name=None, hhs_cache=None)" 
   to download data for a given location and produce .txt files in grassland model input data format.

   Parameters:
   - coordinates (dict): Dictionary with "lat" and "lon" keys ({'lat': float, 'lon': float}).
   - file_name (str or Path): File name to save soil data (optional, default file name is used if not provided).
   - hhs_cache (Path): Path for local HiHydroSoil map directory (optional).