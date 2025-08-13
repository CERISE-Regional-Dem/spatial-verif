import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys
import re
import os

# This script is adapted from dump_cerise.py to handle ISBA data.
# Example usage: python dump_isba.py /path/to/your/SURFOUT.20180601_12h00.nc

input_file = str(sys.argv[1])  # Full path to the input NetCDF file

# Open the NetCDF file
isba_analysis = xr.open_dataset(input_file)

def extract_timestamp_from_path(file_path):
    """
    Extract timestamp from file path pattern:
    /path/to/YYYY/MM/DD/HH/MMM/SURFOUT.YYYYMMDD_HHhMM.nc
    Returns: YYYYMMDDHHHHMM (e.g., 2018062800003)
    """
    try:
        # Extract components from the path
        path_parts = file_path.split('/')
        
        # Find the date components in the path (YYYY/MM/DD/HH)
        year = month = day = init_hour = None
        for i, part in enumerate(path_parts):
            if len(part) == 4 and part.isdigit() and 2000 <= int(part) <= 2100:  # Year
                year = part
                if i + 3 < len(path_parts):
                    month = path_parts[i + 1]
                    day = path_parts[i + 2] 
                    init_hour = path_parts[i + 3]
                break
        
        # Extract forecast hour from filename
        filename = os.path.basename(file_path)
        forecast_match = re.search(r'_(\d{2})h(\d{2})\.nc$', filename)
        
        if year and month and day and init_hour and forecast_match:
            forecast_hour = forecast_match.group(1)
            forecast_min = forecast_match.group(2)
            
            # Format: YYYYMMDDHHHHMM
            #timestamp = f"{year}{month.zfill(2)}{day.zfill(2)}{init_hour.zfill(2)}{forecast_hour.zfill(3)}{forecast_min.zfill(2)}"
            timestamp = f"{year}{month}{day}{init_hour}{forecast_hour}"
            return timestamp
        else:
            # Fallback: try to extract from filename only
            filename_match = re.search(r'SURFOUT\.(\d{8})_(\d{2})h(\d{2})\.nc$', filename)
            if filename_match:
                date_part = filename_match.group(1)  # YYYYMMDD
                hour_part = filename_match.group(2)  # HH
                min_part = filename_match.group(3)   # MM
                # We don't have init hour from filename, so use 00 as default
                timestamp = f"{date_part}00{hour_part.zfill(3)}{min_part.zfill(2)}"
                return timestamp
                
    except Exception as e:
        print(f"Warning: Could not extract timestamp from path: {e}")
    
    return None

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
output_filename = "isba_binnary.nc"
timestamp = extract_timestamp_from_path(input_file)
output_filename = f"isba_binnary_{timestamp}.nc"

dump_subset(isba_subset, output_filename)
