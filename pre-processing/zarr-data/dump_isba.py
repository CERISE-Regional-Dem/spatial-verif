import xarray as xr
import numpy as np
import datetime
import pandas as pd
import sys
import re
import os

"""
Create a CARRA-like NetCDF from the SURFOUT file dumping the variable DSN_T_ISBA
- Use integer dimensions y, x with 1D coordinate variables
- Provide data variable bin_snow(y, x)
- Provide 2D auxiliary variables x_2d(y,x) and y_2d(y,x) for actual coordinates
- Provide 1D coordinate variables x(x) and y(y) for dimension coordinates
- Provide a scalar 'crs' variable with LCC attributes (typical for CARRA Greenland)
- Populate global attributes sensibly

Usage:
    python dump_isba_to_carra_like.py /path/to/SURFOUT.YYYYMMDD_HHhMM.nc /output/path
"""

# Args
input_file = str(sys.argv[1])
output_path = str(sys.argv[2])

# Load the file that contains DSN_T_ISBA data from 
isba = xr.open_dataset(input_file)

# Helper: timestamp from path
def extract_timestamp_from_path(file_path):
    try:
        path_parts = file_path.split('/')
        year = month = day = init_hour = None
        for i, part in enumerate(path_parts):
            if len(part) == 4 and part.isdigit() and 2000 <= int(part) <= 2100:
                year = part
                if i + 3 < len(path_parts):
                    month = path_parts[i + 1]
                    day = path_parts[i + 2]
                    init_hour = path_parts[i + 3]
                break
        filename = os.path.basename(file_path)
        m = re.search(r'_(\d{2})h(\d{2})\.nc$', filename)
        if year and month and day and init_hour and m:
            fh, fm = m.group(1), m.group(2)
            return f"{year}{month}{day}{init_hour}{fh}{fm}"
        m2 = re.search(r'SURFOUT\.(\d{8})_(\d{2})h(\d{2})\.nc$', filename)
        if m2:
            d, h, mm = m2.groups()
            return f"{d}00{h}{mm}"
    except Exception as e:
        print(f"Warning: Could not extract timestamp: {e}")
    return None

# Determine native grid dims and build CARRA-like y/x
# ISBA often uses (yy, xx). Rename to internal y/x to work easily
work = isba
if 'yy' in work.sizes and 'xx' in work.sizes:
    work = work.rename({'yy': 'y', 'xx': 'x'})

ny = work.sizes.get('y') or list(work.sizes.values())[0]
nx = work.sizes.get('x') or list(work.sizes.values())[1]

# Build bin_snow from DSN_T_ISBA
if 'DSN_T_ISBA' not in work.variables:
    raise ValueError("Expected variable 'DSN_T_ISBA' not found in input file")

bin_snow = xr.where(work['DSN_T_ISBA'] > 0.01, 1, 0).astype('int64')

# Create output Dataset with proper dimensions and coordinate variables
out = xr.Dataset()

# Create 1D coordinate variables for dimensions
# These will be simple indices or regular grid coordinates
if 'XX' in work.variables and 'YY' in work.variables:
    XX = work['XX'].values
    YY = work['YY'].values
    # Try to extract 1D coordinates from 2D arrays if they're regular
    x_1d = XX[0, :] if XX.ndim == 2 else XX
    y_1d = YY[:, 0] if YY.ndim == 2 else YY
else:
    # Create regular 1D coordinate arrays
    dx = 1000.0  # 1 km spacing
    dy = 1000.0
    x0 = 0.0
    y0 = 0.0
    x_1d = x0 + np.arange(nx) * dx
    y_1d = y0 + np.arange(ny) * dy

# Create the dataset with proper 1D coordinate variables
out = out.assign_coords({
    'x': ('x', x_1d.astype('float32')),
    'y': ('y', y_1d.astype('float32'))
})

# Attach the data
out['bin_snow'] = (('y', 'x'), bin_snow.values)

# Create 2D auxiliary coordinate variables with different names
# These store the actual 2D coordinate fields if needed
if 'XX' in work.variables and 'YY' in work.variables:
    XX = work['XX'].values
    YY = work['YY'].values
    # Ensure shapes match
    if XX.shape != (ny, nx):
        XX = np.broadcast_to(XX, (ny, nx))
    if YY.shape != (ny, nx):
        YY = np.broadcast_to(YY, (ny, nx))
else:
    # Create 2D meshgrid from 1D coordinates
    XX, YY = np.meshgrid(x_1d, y_1d)

# Add 2D auxiliary coordinates with different names to avoid conflict
out['x_2d'] = (('y', 'x'), XX.astype('float32'))
out['y_2d'] = (('y', 'x'), YY.astype('float32'))

# Add a scalar CRS variable with typical CARRA LCC parameters
out['crs'] = xr.DataArray(0, attrs={
    'grid_mapping_name': 'lambert_conformal_conic',
    'latitude_of_projection_origin': 80.0,
    'standard_parallel': [80.0, 80.0],
    'longitude_of_central_meridian': -34.0,
    'false_easting': 0.0,
    'false_northing': 0.0,
    'semi_major_axis': 6371000.0,
    'proj_string': '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0',
})

# Attributes for data variable
out['bin_snow'].attrs.update({
    'standard_name': 'binary_snow_classification',
    'long_name': 'Binary classification of snow presence from ISBA',
    'units': '1',
    'valid_min': np.int64(0),
    'valid_max': np.int64(1),
    'grid_mapping': 'crs',
    'coordinates': 'x_2d y_2d',  # Point to the 2D auxiliary coordinates
})

# Attributes for 1D coordinate variables
out['x'].attrs.update({
    'standard_name': 'projection_x_coordinate',
    'long_name': 'x coordinate of projection',
    'units': 'm',
    'axis': 'X',
})

out['y'].attrs.update({
    'standard_name': 'projection_y_coordinate',
    'long_name': 'y coordinate of projection',
    'units': 'm',
    'axis': 'Y',
})

# Attributes for 2D auxiliary coordinate variables
out['x_2d'].attrs.update({
    'standard_name': 'projection_x_coordinate',
    'long_name': '2D x coordinate of projection',
    'units': 'm',
})

out['y_2d'].attrs.update({
    'standard_name': 'projection_y_coordinate',
    'long_name': '2D y coordinate of projection',
    'units': 'm',
})

# Global attributes
out.attrs.update({
    'Conventions': 'CF-1.7',
    'title': 'Binary Snow from ISBA (CARRA-like grid, no template)',
    'institution': 'Unknown',
    'source': 'ISBA model output',
    'history': f'Created on {datetime.datetime.now().strftime("%Y-%m-%d")} from {input_file}',
})

# Encoding and writing
encoding = {
    'bin_snow': {'zlib': True, 'complevel': 4},
    'x': {'zlib': True, 'complevel': 4},
    'y': {'zlib': True, 'complevel': 4},
    'x_2d': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(np.nan)},
    'y_2d': {'zlib': True, 'complevel': 4, '_FillValue': np.float32(np.nan)},
}

# Name the file
timestamp = extract_timestamp_from_path(input_file)
if timestamp:
    out_name = f"isba_binnary_{timestamp[:-2]}.nc" if len(timestamp) >= 12 else f"isba_binnary_{timestamp}.nc"
else:
    out_name = "isba_binnary.nc"

out_path = os.path.join(output_path, out_name)

# Write to NetCDF
out.to_netcdf(out_path, format='NETCDF4', encoding=encoding)
print(f"Created file: {out_path}")

# Close
isba.close()
