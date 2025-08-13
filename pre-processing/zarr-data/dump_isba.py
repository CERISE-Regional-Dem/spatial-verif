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

# Example usage: python dump_isba.py /path/to/SURFOUT.20180628_03h00.nc

input_file = str(sys.argv[1])  # Full path to the input NetCDF file
output_path = str(sys.argv[2])  # Path of the output files

# Open the NetCDF file
isba_analysis = xr.open_dataset(input_file)

def extract_timestamp_from_path(file_path):
    """
    Extract timestamp from file path pattern like:
      /.../YYYY/MM/DD/HH/MMM/SURFOUT.YYYYMMDD_HHhMM.nc
    Returns: YYYYMMDD + initHH + forecastHH + forecastMM
      e.g., 20180628 + 00 + 03 + 00 -> 20180628000300
    If path is different, falls back to filename-only parsing (initHH assumed 00).
    """
    try:
        # Extract components from the path
        path_parts = file_path.split('/')

        # Find the date components in the path (YYYY/MM/DD/HH)
        year = month = day = init_hour = None
        for i, part in enumerate(path_parts):
            if len(part) == 4 and part.isdigit() and 2000 <= int(part) <= 2100:  # Year folder
                year = part
                if i + 3 < len(path_parts):
                    month = path_parts[i + 1]
                    day = path_parts[i + 2]
                    init_hour = path_parts[i + 3]
                break

        # Extract forecast hour and minutes from filename
        filename = os.path.basename(file_path)
        # Matches _03h00.nc -> groups: 03, 00
        forecast_match = re.search(r'_(\d{2})h(\d{2})\.nc$', filename)

        if year and month and day and init_hour and forecast_match:
            forecast_hour = forecast_match.group(1)  # two digits
            forecast_min = forecast_match.group(2)   # two digits

            # If you prefer YYYYMMDD + initHH + forecastHH (no minutes), drop forecast_min below
            #timestamp = f"{year}{month.zfill(2)}{day.zfill(2)}{init_hour.zfill(2)}{forecast_hour.zfill(2)}{forecast_min.zfill(2)}"
            timestamp = f"{year}{month}{day}{init_hour}{forecast_hour}"
            return timestamp
        else:
            # Fallback: try to extract from filename only
            filename_match = re.search(r'SURFOUT\.(\d{8})_(\d{2})h(\d{2})\.nc$', filename)
            if filename_match:
                date_part = filename_match.group(1)   # YYYYMMDD
                hour_part = filename_match.group(2)   # HH
                min_part = filename_match.group(3)    # MM
                # No init hour in filename -> assume 00
                timestamp = f"{date_part}00{hour_part.zfill(2)}{min_part.zfill(2)}"
                return timestamp

    except Exception as e:
        print(f"Warning: Could not extract timestamp from path: {e}")

    return None

# Create the 'bin_snow' variable based on 'DSN_T_ISBA'
isba_subset = isba_analysis.copy()
isba_subset["bin_snow"] = xr.where(isba_subset["DSN_T_ISBA"] > 0.01, 1, 0)

# Rename the primary grid dimensions to CF-friendly names
# Original dims are 'yy' and 'xx' in your file (order: (yy, xx))
if 'yy' in isba_subset.dims and 'xx' in isba_subset.dims:
    isba_subset = isba_subset.rename({'yy': 'y', 'xx': 'x'})

# Build 1D x and y coordinate variables from the 2D XX/YY if available
# This helps programs that expect 1D CF coordinates with the proper standard_name.
if 'XX' in isba_subset and 'YY' in isba_subset:
    try:
        # XX and YY are (y, x). Derive 1D x from first row and 1D y from first column.
        x_1d = xr.DataArray(isba_subset['XX'].isel(y=0).values, dims=('x',))
        y_1d = xr.DataArray(isba_subset['YY'].isel(x=0).values, dims=('y',))

        # Assign as coordinate variables named 'x' and 'y'
        isba_subset = isba_subset.assign_coords({'x': x_1d, 'y': y_1d})
    except Exception as e:
        print(f"Warning: Could not derive 1D x/y from XX/YY: {e}")

def dump_subset(subset_ds, output_file='binary_snow_classification_isba.nc'):
    # Keep the snow classification and ensure we have the 1D x/y coords present.
    keep_vars = ['bin_snow']
    if 'x' in subset_ds.coords:
        keep_vars.append('x')
    if 'y' in subset_ds.coords:
        keep_vars.append('y')

    # Optionally keep 2D XX/YY as auxiliary if you want
    if 'XX' in subset_ds:
        keep_vars.append('XX')
    if 'YY' in subset_ds:
        keep_vars.append('YY')

    subset_ds = subset_ds[keep_vars]

    # Ensure x/y are coordinates (not data variables)
    coords_to_set = [c for c in ['x', 'y'] if c in subset_ds]
    if coords_to_set:
        subset_ds = subset_ds.set_coords(coords_to_set)

    # Add a dummy crs variable
    subset_ds['crs'] = xr.DataArray(0, name='crs')

    # Add CF-1.7 compliant attributes for projected coordinates
    if 'x' in subset_ds.coords:
        subset_ds['x'].attrs = {
            'standard_name': 'projection_x_coordinate',
            'long_name': 'x coordinate of projection',
            'units': 'm',
            'axis': 'X',
            'grid_mapping': 'crs'
        }

    if 'y' in subset_ds.coords:
        subset_ds['y'].attrs = {
            'standard_name': 'projection_y_coordinate',
            'long_name': 'y coordinate of projection',
            'units': 'm',
            'axis': 'Y',
            'grid_mapping': 'crs'
        }

    # If keeping auxiliary 2D coordinates, keep their attrs lightweight
    if 'XX' in subset_ds:
        subset_ds['XX'].attrs = {
            'long_name': 'x coordinate (2D auxiliary)',
            'units': 'm',
            'grid_mapping': 'crs'
        }
    if 'YY' in subset_ds:
        subset_ds['YY'].attrs = {
            'long_name': 'y coordinate (2D auxiliary)',
            'units': 'm',
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

    # Add proper CRS attributes (adjust if your true projection differs)
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

    # Global attributes
    subset_ds.attrs.update({
        'Conventions': 'CF-1.7',
        'title': 'Binary Snow from ISBA',
        'institution': 'Unknown',
        'source': 'ISBA model output',
        'history': f'Created on {datetime.datetime.now().strftime("%Y-%m-%d")} from {input_file}',
    })

    # Write to netCDF file
    encoding = {
        'bin_snow': {'zlib': True, 'complevel': 4}
    }
    if 'x' in subset_ds.coords:
        encoding['x'] = {'zlib': True, 'complevel': 4}
    if 'y' in subset_ds.coords:
        encoding['y'] = {'zlib': True, 'complevel': 4}
    subset_ds = subset_ds.rename({'XX': 'X', 'YY': 'Y'})
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding=encoding)
    print(f"Created file: {output_file}")

# Generate output filename based on file path timestamp
timestamp = extract_timestamp_from_path(input_file)
if timestamp:
    output_filename = f"isba_{timestamp}.nc"
else:
    # Fallback to original logic if Dataset has 'time'
    output_filename = "isba_binned.nc"
    if hasattr(isba_subset, 'time'):
        try:
            time_str = pd.to_datetime(isba_subset.time.values[0]).strftime('%Y%m%d')
            output_filename = f"isba_{time_str}.nc"
        except Exception:
            pass
output_filename = os.path.join(output_path,output_filename)
dump_subset(isba_subset, output_filename)
