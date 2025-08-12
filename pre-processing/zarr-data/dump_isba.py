
import xarray as xr
import numpy as np

import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime

import pandas as pd

import sys

# This script is adapted from dump_cerise.py to handle ISBA data.
# Example usage: python dump_isba.py /path/to/your/@SURFOUT.20180601_12h00.nc

input_file = str(sys.argv[1]) # Full path to the input NetCDF file

# Open the NetCDF file
isba_analysis = xr.open_dataset(input_file)

# In dump_cerise.py, 'hxa' was used. Here we use 'DSN_T_ISBA'.
# Create the 'bin_snow' variable based on 'DSN_T_ISBA'
# The logic is the same as in dump_cerise.py: snow presence if value > 0.01
isba_subset = isba_analysis.copy() # Create a copy to avoid modifying the original dataset
isba_subset["bin_snow"]  = xr.where(isba_subset["DSN_T_ISBA"] > 0.01, 1, 0)  

def dump_subset(subset_ds,output_file = 'binary_snow_classification_isba.nc'):
    # Select only the variables we want to keep
    # Assuming DSN_T_ISBA is on a lat/lon grid, but we will add projection info
    # to match the cerise data.
    subset_ds = subset_ds[['bin_snow', 'latitude', 'longitude']]
    
    # Rename for consistency if needed, assuming 'latitude' and 'longitude' exist
    if 'latitude' in subset_ds.coords and 'longitude' in subset_ds.coords:
        subset_ds = subset_ds.rename({'latitude': 'lat', 'longitude': 'lon'})

    # Add a dummy crs variable that we will populate with attributes
    subset_ds['crs'] = xr.DataArray(0, name='crs')

    # Add CF-1.7 compliant attributes for coordinates
    subset_ds['lat'].attrs = {
        'standard_name': 'latitude',
        'long_name': 'latitude',
        'units': 'degrees_north',
        'axis': 'Y',
        'valid_min': -90.0,
        'valid_max': 90.0,
        'grid_mapping': 'crs'
    }
    
    subset_ds['lon'].attrs = {
        'standard_name': 'longitude',
        'long_name': 'longitude',
        'units': 'degrees_east',
        'axis': 'X',
        'valid_min': -180.0,
        'valid_max': 180.0,
        'grid_mapping': 'crs'
    }
    
    # Add attributes for bin_snow
    subset_ds['bin_snow'].attrs.update({
        'standard_name': 'binary_snow_classification',
        'long_name': 'Binary classification of snow presence from ISBA',
        'units': '1',  # dimensionless
        'valid_min': 0,
        'valid_max': 1,
        'grid_mapping': 'crs'
    })
    
    # Add proper CRS attributes, assuming same projection as cerise
    subset_ds['crs'].attrs = {
        'grid_mapping_name': 'lambert_conformal_conic',
        'latitude_of_projection_origin': 80.0,
        'standard_parallel': [80.0, 80.0],
        'longitude_of_central_meridian': -34.0,
        'false_easting': 0.0,
        'false_northing': 0.0,
        'semi_major_axis': 6371000.0,
        'proj_string': '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0',
    }
    
    # Ensure global attributes are CF-1.7 compliant
    subset_ds.attrs.update({
        'Conventions': 'CF-1.7',
        'title': 'Binary Snow from ISBA',
        'institution': 'Unknown', # Please fill in
        'source': 'ISBA model output',
        'history': f'Created on {datetime.datetime.now().strftime("%Y-%m-%d")} from {input_file}',
    })
    
    # Write to netCDF file
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4},
        'lat': {'zlib': True, 'complevel': 4},
        'lon': {'zlib': True, 'complevel': 4},
    })
    
    print(f"Created file: {output_file}")

# For now, this script processes the whole file at once.
# If the file has a time dimension, you might want to loop over it like in dump_cerise.py
# This is a simplified version assuming a single time slice or time-independent data.

# Generate an output filename based on the input
output_filename = "isba_binned.nc"
if hasattr(isba_subset, 'time'):
    # If there is a time dimension, use the first time step for the filename
    try:
        time_str = pd.to_datetime(isba_subset.time.values[0]).strftime('%Y%m%d')
        output_filename = f"isba_{time_str}.nc"
    except:
        pass


dump_subset(isba_subset, output_filename)
