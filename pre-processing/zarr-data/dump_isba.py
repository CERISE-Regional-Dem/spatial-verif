import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys

# This script is adapted from dump_cerise.py to handle ISBA data.
# Example usage: python dump_isba.py /path/to/your/SURFOUT.20180601_12h00.nc

input_file = str(sys.argv[1])  # Full path to the input NetCDF file

# Open the NetCDF file
isba_analysis = xr.open_dataset(input_file)

# Create the 'bin_snow' variable based on 'DSN_T_ISBA'
isba_subset = isba_analysis.copy()
isba_subset["bin_snow"] = xr.where(isba_subset["DSN_T_ISBA"] > 0.01, 1, 0)

def dump_subset(subset_ds, output_file='binary_snow_classification_isba.nc'):
    # The file uses projected coordinates XX, YY instead of lat/lon
    # We need to work with the existing coordinate system
    
    # Select the variables we want to keep, using the actual coordinate names
    subset_ds = subset_ds[['bin_snow', 'XX', 'YY']]
    
    # Rename coordinates to match expected names
    subset_ds = subset_ds.rename({'XX': 'x', 'YY': 'y', 'xx': 'x_dim', 'yy': 'y_dim'})
    
    # Add a dummy crs variable
    subset_ds['crs'] = xr.DataArray(0, name='crs')
    
    # Add CF-1.7 compliant attributes for projected coordinates
    subset_ds['x'].attrs = {
        'standard_name': 'projection_x_coordinate',
        'long_name': 'x coordinate of projection',
        'units': 'm',  # assuming meters for projected coordinates
        'axis': 'X',
        'grid_mapping': 'crs'
    }
    
    subset_ds['y'].attrs = {
        'standard_name': 'projection_y_coordinate', 
        'long_name': 'y coordinate of projection',
        'units': 'm',  # assuming meters for projected coordinates
        'axis': 'Y',
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
    
    # Add proper CRS attributes based on the file's projection info
    # You may need to adjust these based on your actual projection
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
        'institution': 'Unknown',
        'source': 'ISBA model output',
        'history': f'Created on {datetime.datetime.now().strftime("%Y-%m-%d")} from {input_file}',
    })
    
    # Write to netCDF file
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
    })
    
    print(f"Created file: {output_file}")

# Generate output filename
output_filename = "isba_binary.nc"
if hasattr(isba_subset, 'time'):
    try:
        time_str = pd.to_datetime(isba_subset.time.values[0]).strftime('%Y%m%d')
        output_filename = f"isba_{time_str}.nc"
    except:
        pass

dump_subset(isba_subset, output_filename)
