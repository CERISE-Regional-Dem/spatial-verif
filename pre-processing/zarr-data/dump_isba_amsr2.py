import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys
import os
import re

# This script is adapted from dump_cerise.py to handle ISBA data.
# Example usage: python dump_isba.py /path/to/your/SURFOUT.20180601_12h00.nc

def sfx2areadef(lat0: float,
                lon0: float, 
                latc: float, 
                lonc: float, 
                nx: int, 
                ny: int, 
                dx: tuple[int, float]=2500, 
                get_proj: bool=False
                ):
    """Returns pyresample.geometry.AreaDefinition based on surfex domain.
    Supports both lcc and stere (if lat0 == 90)
    
    Args:
        lat0 (float): projection lat0
        lon0 (float): projection lon0
        latc (float): surfex grid center lat
        lonc (float): surfex grid center lon
        nx (int): number of gridpoints x
        ny (int): number of gridpoints y
        dx (int, float, optional): grid spacing [m]. Defaults to 2500.
        get_proj (bool, optional): return pyproj object together with areadefinition. Defaults to False.

    Returns:
        pyresample.geometry.AreaDefinition: 
    """

    proj_type = "lcc" if lat0 < 90 else "stere"
    proj2 = {
        "proj": proj_type,
        "lat_0": lat0,
        "lon_0": lon0,
        "ellps": "WGS84",
        "no_defs": True,
        "units": "m",
    }
    if lat0 < 90:
        proj2["lat_1"] = lat0
        proj2["lat_2"] = lat0
    
    
    p2 = pyproj.Proj(proj2, preserve_units=False)
    center = p2(lonc, latc, inverse=False)
    ll = (center[0] - dx*nx/2, center[1] - dx*ny/2)
    extent = ll + (ll[0] + nx*dx, ll[1] + ny*dx)
    if get_proj:
        return pyresample.geometry.AreaDefinition("0", "domain", proj_type, proj2, nx, ny, extent), p2
    return pyresample.geometry.AreaDefinition("0", "domain", proj_type, proj2, nx, ny, extent)

input_file = str(sys.argv[1])  # Full path to the input NetCDF file
output_path = str(sys.argv[2])


# Open the NetCDF file
isba_analysis = xr.open_dataset(input_file)

# Create the 'bin_snow' variable based on 'DSN_T_ISBA'
isba_subset = isba_analysis.copy()
isba_subset["bin_snow"] = xr.where(isba_subset["DSN_T_ISBA"] > 0.01, 1, 0)

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
            return f"{year}{month}{day}{init_hour}{fh}"
        m2 = re.search(r'SURFOUT\.(\d{8})_(\d{2})h(\d{2})\.nc$', filename)
        if m2:
            d, h, mm = m2.groups()
            return f"{d}00{h}{mm}"
    except Exception as e:
        print(f"Warning: Could not extract timestamp: {e}")
    return None

def parse_timestamp_to_datetime(timestamp_str):
    """Parse timestamp string to datetime object.
    
    Args:
        timestamp_str (str): Timestamp in format like '2018060100120' 
                            (YYYYMMDDHHMM + optional forecast hour)
    
    Returns:
        datetime.datetime: Parsed datetime object
    """
    if not timestamp_str:
        return None
    
    try:
        # Handle different timestamp formats
        if len(timestamp_str) >= 12:
            # Extract YYYYMMDDHHMM (first 12 characters)
            date_part = timestamp_str[:12]
            year = int(date_part[:4])
            month = int(date_part[4:6])
            day = int(date_part[6:8])
            hour = int(date_part[8:10])
            minute = int(date_part[10:12])
            
            # If there are additional characters, they might represent forecast hours
            if len(timestamp_str) > 12:
                forecast_hour = int(timestamp_str[12:])
                base_time = datetime.datetime(year, month, day, hour, minute)
                return base_time + datetime.timedelta(hours=forecast_hour)
            else:
                return datetime.datetime(year, month, day, hour, minute)
        else:
            # Fallback for shorter timestamps
            return datetime.datetime.now()
            
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse timestamp '{timestamp_str}': {e}")
        return None

def dump_subset(subset_ds, output_file='binary_snow_classification_isba.nc', timestamp_str=None):
    # Extract projection parameters from the source dataset
    lat0 = float(subset_ds['LAT0'].values)
    lon0 = float(subset_ds['LON0'].values)
    latori = 74 # float(subset_ds['LATORI'].values) harcoded to use values suggested by Aasmund
    lonori = 26 # float(subset_ds['LONORI'].values) hardcoded values following aasmund

    # Get grid dimensions from XX variable
    ny, nx = subset_ds['XX'].shape

    # Define grid spacing (dx). Default is 2500m.
    dx = 2500

    # Use sfx2areadef to get the correct projection and grid definition
    # latc and lonc are the center of the grid
    area_def = sfx2areadef(lat0, lon0, latori, lonori, nx, ny, dx=dx, get_proj=False)

    # Get the 1D coordinate arrays from the area definition
    proj_y_2d, proj_x_2d = area_def.get_proj_coords()
    x_1d = proj_x_2d[0, :]
    y_1d = proj_y_2d[:, 0]
    
    # Parse timestamp to datetime
    dt = parse_timestamp_to_datetime(timestamp_str)
    if dt is None:
        dt = datetime.datetime.now()
        print(f"Warning: Using current time as fallback: {dt}")
    
    # Create a new dataset with proper dimensions and coordinates
    new_ds = xr.Dataset()
    
    # Create proper 1D coordinate variables
    new_ds['x'] = xr.DataArray(x_1d, dims=['x'], name='x')
    new_ds['y'] = xr.DataArray(y_1d, dims=['y'], name='y')
    
    # Add time coordinate
    dt_fix = datetime.datetime(dt.year,dt.month,dt.day,6,0)
    new_ds['time'] = xr.DataArray([dt_fix], dims=['time'], name='time')
    
    # Add the bin_snow variable with proper dimensions including time
    new_ds['bin_snow'] = xr.DataArray(
       #subset_ds['bin_snow'].values[::-1], #gotta flip the field as well!
       subset_ds['bin_snow'].values[np.newaxis, :, :],  # Add time dimension
        dims=['time', 'y', 'x'],
        coords={'time': new_ds['time'], 'y': new_ds['y'], 'x': new_ds['x']},
        name='bin_snow'
    )
    
    # Add a dummy crs variable
    new_ds['crs'] = xr.DataArray(0, name='crs')
    
    # Add CF-1.7 compliant attributes for projected coordinates
    new_ds['x'].attrs = {
        'standard_name': 'projection_x_coordinate',
        'long_name': 'x coordinate of projection',
        'units': 'm',  # assuming meters for projected coordinates
        'axis': 'X'
    }
    
    new_ds['y'].attrs = {
        'standard_name': 'projection_y_coordinate', 
        'long_name': 'y coordinate of projection',
        'units': 'm',  # assuming meters for projected coordinates
        'axis': 'Y'
    }
    
    # Add time attributes
    new_ds['time'].attrs = {
        'standard_name': 'time',
        'long_name': 'time',
        'axis': 'T'
    }
    
    # Add attributes for bin_snow
    new_ds['bin_snow'].attrs = {
        'standard_name': 'binary_snow_classification',
        'long_name': 'Binary classification of snow presence from ISBA',
        'units': '1',  # dimensionless
        'valid_min': 0,
        'valid_max': 1,
        'grid_mapping': 'crs'
    }
    
    # Add proper CRS attributes based on the actual file's projection info
    # For Lambert Conformal Conic with the extracted parameters
    new_ds['crs'].attrs = {
        'grid_mapping_name': 'lambert_conformal_conic',
        'latitude_of_projection_origin': lat0,  # LAT0 = 80
        'standard_parallel': [lat0, lat0],  # Using LAT0 for both standard parallels
        'longitude_of_central_meridian': lon0,  # LON0 = -34
        'false_easting': 0.0,
        'false_northing': 0.0,
        'semi_major_axis': 6371000.0,  # Standard Earth radius
        'proj_string': f'+R=6371000 +lat_0={lat0} +lat_1={lat0} +lat_2={lat0} +lon_0={lon0} +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0',
    }
    
    # Ensure global attributes are CF-1.7 compliant
    new_ds.attrs = {
        'Conventions': 'CF-1.7',
        'title': 'Binary Snow from ISBA',
        'institution': 'Unknown',
        'source': 'ISBA model output',
        'history': f'Created on {datetime.datetime.now().strftime("%Y-%m-%d")} from {input_file}',
        'original_projection': f'Lambert Conformal Conic (LAT0={lat0}, LON0={lon0}, LATORI={latori}, LONORI={lonori})',
        'reference_time': dt_fix.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write to netCDF file
    new_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
        'time': {'units': 'seconds since 1970-01-01 00:00:00', 'calendar': 'gregorian'}
    })
    
    print(f"Created file: {output_file}")
    print(f"Time: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Projection: Lambert Conformal Conic")
    print(f"  - Central latitude: {lat0}°")
    print(f"  - Central longitude: {lon0}°")
    print(f"  - Origin latitude: {latori}°")
    print(f"  - Origin longitude: {lonori}°")

# Generate output filename
#output_filename = "isba_binary.nc"
# Name the file
timestamp = extract_timestamp_from_path(input_file)

if timestamp:
    output_filename = f"isba_binary_{timestamp[:-2]}.nc" if len(timestamp) >= 12 else f"isba_binary_{timestamp}.nc"
else:
    output_filename = "isba_binary.nc"

output_filename = os.path.join(output_path, output_filename)

dump_subset(isba_subset, output_filename, timestamp)
