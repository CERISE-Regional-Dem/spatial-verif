import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys
from datetime import timezone
import uuid
import os

date_ini = str(sys.argv[1])  # "2016-09-01"
date_end = sys.argv[2]
out_path = sys.argv[3]

# ims = xr.open_zarr("/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/ims.zarr")
ims = xr.open_zarr("/scratch/fab0/Projects/cerise/carra_snow_data/ims.zarr")

ims["bin_snow"] = xr.where(ims["IMS_Surface_Values"] == 4, 1, 0)

# Create new coordinates based on dimension sizes
new_x = np.arange(ims.dims['x'])  # Will create array from 0 to 799
new_y = np.arange(ims.dims['y'])  # Will create array from 0 to 999

# Assign new coordinates to the dataset
ims["x"] = np.arange(ims.dims['x'])
ims["y"] = np.arange(ims.dims['y'])

date_range = ims.sel(time=slice(date_ini, date_end))

def create_proper_projection_coords(ds):
    """
    Create proper projection coordinates following the same approach as extract_snow_data_cf.py
    Using the IMS projection parameters from the original data
    """
    # IMS uses Lambert Conformal Conic with these parameters (from original attributes)
    # Based on the proj_string in the original code:
    # '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0'
    
    # Extract grid information
    ny, nx = ds.dims['y'], ds.dims['x']
    
    # From the bounding box in original: [537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063]
    # Calculate grid spacing
    x_min, y_min, x_max, y_max = 537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063
    dx = (x_max - x_min) / nx  # Should be 2500m
    dy = (y_max - y_min) / ny  # Should be 2500m
    
    # Create coordinate arrays in projection space (meters)
    x_coords = np.linspace(x_min + dx/2, x_max - dx/2, nx)  # Cell centers
    y_coords = np.linspace(y_min + dy/2, y_max - dy/2, ny)  # Cell centers
    
    return x_coords, y_coords, dx

def calculate_lonlat_coords(x_coords, y_coords):
    """
    Calculate longitude/latitude coordinates from projection coordinates
    """
    # Define the IMS projection
    proj_dict = {
        "proj": "lcc",
        "lat_0": 80.0,
        "lat_1": 80.0, 
        "lat_2": 80.0,
        "lon_0": -34.0,
        "R": 6371000.0,
        "x_0": 0.0,
        "y_0": 0.0,
        "units": "m",
        "no_defs": True
    }
    
    transformer = pyproj.Transformer.from_proj(
        pyproj.Proj(proj_dict),
        pyproj.Proj('EPSG:4326'),  # WGS84
        always_xy=True
    )
    
    # Create meshgrid
    X, Y = np.meshgrid(x_coords, y_coords)
    
    # Transform to lon/lat
    lons, lats = transformer.transform(X, Y)
    
    return lons, lats

def dump_subset_cf_compliant(ds, output_file='binary_snow_classification.nc'):
    """
    Create CF-compliant NetCDF following the same standards as extract_snow_data_cf.py
    """
    # Get proper projection coordinates
    x_coords, y_coords, dx = create_proper_projection_coords(ds)
    
    # Calculate longitude/latitude
    lons, lats = calculate_lonlat_coords(x_coords, y_coords)
    
    # Extract time
    time_val = ds.time.values
    dt = pd.to_datetime(time_val).to_pydatetime()
    
    # Create projection variable with comprehensive CF attributes
    proj_var = xr.DataArray(
        data=np.array([], dtype='c'),  # Empty array for grid mapping variable
        attrs={
            'grid_mapping_name': 'lambert_conformal_conic',
            'longitude_of_central_meridian': -34.0,
            'latitude_of_projection_origin': 80.0,
            'standard_parallel': [80.0, 80.0],
            'false_easting': 0.0,
            'false_northing': 0.0,
            'semi_major_axis': 6371000.0,  # Sphere radius from IMS
            'proj_string': '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0'
        }
    )
    
    # Create time bounds for CF compliance
    time_bounds = xr.DataArray(
        data=np.array([[dt, dt]]),
        dims=['time', 'nv'],
        attrs={'long_name': 'time bounds'}
    )
    
    # Create coordinate variables with proper CF attributes
    time_coord = xr.DataArray(
        data=[dt],
        dims=['time'],
        attrs={
            'long_name': 'time',
            'standard_name': 'time',
            'bounds': 'time_bnds',
            'axis': 'T'
        }
    )
    
    x_coord = xr.DataArray(
        data=x_coords,
        dims=['x'],
        attrs={
            'long_name': 'x coordinate of projection',
            'standard_name': 'projection_x_coordinate',
            'units': 'm',
            'axis': 'X'
        }
    )
    
    y_coord = xr.DataArray(
        data=y_coords,
        dims=['y'],
        attrs={
            'long_name': 'y coordinate of projection', 
            'standard_name': 'projection_y_coordinate',
            'units': 'm',
            'axis': 'Y'
        }
    )
    
    # Longitude coordinate variable
    longitude_var = xr.DataArray(
        data=lons,
        dims=['y', 'x'],
        attrs={
            'long_name': 'longitude',
            'standard_name': 'longitude',
            'units': 'degrees_east',
            'valid_min': -180.0,
            'valid_max': 180.0
        }
    )
    
    # Latitude coordinate variable
    latitude_var = xr.DataArray(
        data=lats,
        dims=['y', 'x'],
        attrs={
            'long_name': 'latitude',
            'standard_name': 'latitude', 
            'units': 'degrees_north',
            'valid_min': -90.0,
            'valid_max': 90.0
        }
    )
    
    # Binary snow variable with comprehensive CF attributes
    bin_snow_var = xr.DataArray(
        data=ds['bin_snow'].values[np.newaxis, :, :],  # Add time dimension
        dims=['time', 'y', 'x'],
        attrs={
            'long_name': 'Binary snow cover classification',
            'standard_name': 'binary_snow_classification',
            'units': '1',
            'valid_min': 0,
            'valid_max': 1,
            'flag_values': [0, 1],
            'flag_meanings': 'no_snow snow',
            '_FillValue': -1,
            'missing_value': -1,
            'grid_mapping': 'lambert_conformal_conic',
            'coordinates': 'longitude latitude',
            'cell_methods': 'time: point',
            'comment': 'Binary snow cover from IMS (Interactive Multisensor Snow and Ice Mapping System). Value 1 indicates snow presence (IMS_Surface_Values == 4), 0 indicates no snow.',
            'source': 'IMS (Interactive Multisensor Snow and Ice Mapping System)'
        }
    )
    
    # Create the CF-compliant dataset
    subset_ds = xr.Dataset(
        data_vars={
            'bin_snow': bin_snow_var,
            'lambert_conformal_conic': proj_var,
            'longitude': longitude_var,
            'latitude': latitude_var,
            'time_bnds': time_bounds
        },
        coords={
            'time': time_coord,
            'x': x_coord,
            'y': y_coord,
            'nv': xr.DataArray([0, 1], dims=['nv'])
        }
    )
    
    # Add comprehensive global attributes following the same pattern as extract_snow_data_cf.py
    creation_time = datetime.datetime.now(timezone.utc)
    unique_id = str(uuid.uuid4())
    
    subset_ds.attrs = {
        # CF Convention requirements
        'Conventions': 'CF-1.8',
        
        # Dataset identification and description
        'title': 'Binary Snow Cover from IMS (Interactive Multisensor Snow and Ice Mapping System)',
        'summary': 'Binary snow cover classification derived from IMS snow and ice mapping data. Values indicate presence (1) or absence (0) of snow.',
        'keywords': 'snow, snow cover, binary classification, IMS, remote sensing, cryosphere',
        'keywords_vocabulary': 'GCMD Science Keywords',
        
        # Dataset identification
        'id': unique_id,
        'naming_authority': 'local',
        'creator_name': 'CERISE Processing System',
        'creator_type': 'person',
        'creator_institution': 'DMI/Met Norway',
        'publisher_name': 'CERISE',
        'publisher_type': 'institution', 
        'publisher_institution': 'DMI/Met Norway',
        
        # Temporal coverage
        'time_coverage_start': dt.isoformat() + 'Z',
        'time_coverage_end': dt.isoformat() + 'Z',
        'time_coverage_duration': 'PT0S',
        'time_coverage_resolution': 'PT0S',
        
        # Spatial coverage
        'geospatial_lat_min': float(lats.min()),
        'geospatial_lat_max': float(lats.max()),
        'geospatial_lon_min': float(lons.min()),
        'geospatial_lon_max': float(lons.max()),
        'geospatial_lat_units': 'degrees_north',
        'geospatial_lon_units': 'degrees_east',
        'geospatial_vertical_min': 0.0,
        'geospatial_vertical_max': 0.0,
        'geospatial_vertical_units': 'm',
        'geospatial_vertical_positive': 'up',
        
        # Processing and source information
        'source': 'IMS (Interactive Multisensor Snow and Ice Mapping System)',
        'processing_level': 'Level 2',
        'product_version': '1.0',
        'references': 'https://www.natice.noaa.gov/ims/',
        'comment': 'Binary snow cover classification where snow pixels (IMS_Surface_Values == 4) are set to 1, all others to 0',
        'acknowledgment': 'NOAA National Ice Center IMS',
        
        # Technical metadata
        'date_created': creation_time.isoformat() + 'Z',
        'date_modified': creation_time.isoformat() + 'Z',
        'date_metadata_modified': creation_time.isoformat() + 'Z',
        'history': f'{creation_time.isoformat()}Z: Binary snow cover extracted from IMS data using snow classification (IMS_Surface_Values == 4)',
        'institution': 'DMI/Met Norway',
        'program': 'CERISE',
        'platform': 'Multiple satellites and surface observations',
        'instrument': 'Multiple sensors',
        
        # File format and standards compliance
        'cdm_data_type': 'Grid',
        'standard_name_vocabulary': 'CF Standard Name Table v79',
        'license': 'Not specified - please check with data provider',
        
        # Grid information - using same format as extract_snow_data_cf.py
        'grid_mapping_name': 'lambert_conformal_conic',
        'projection_lat0': 80.0,
        'projection_lon0': -34.0,
        'grid_spacing_m': dx,
        'grid_size_x': len(x_coords),
        'grid_size_y': len(y_coords),
        'bounding_box': [x_coords.min(), y_coords.min(), x_coords.max(), y_coords.max()],
        
        # Model evaluation tool compatibility
        'project': 'CERISE',
        'dataset': 'IMS',
        'mip': 'obs',
        'realm': 'land',
        'frequency': 'fx',
        'modeling_realm': 'land',
        'table_id': 'fx',
        'variable_id': 'bin_snow',
        'cf_standard_name': 'binary_snow_classification',
        'cell_methods': 'time: point',
        'cell_measures': ''
    }
    
    # Set encoding following the same pattern as extract_snow_data_cf.py
    time_reference = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    encoding = {
        'bin_snow': {
            'zlib': True,
            'complevel': 4,
            'shuffle': True,
            'chunksizes': (1, min(len(y_coords), 256), min(len(x_coords), 256)),
            'dtype': 'int8'
        },
        'longitude': {
            'zlib': True,
            'complevel': 4,
            'dtype': 'float32'
        },
        'latitude': {
            'zlib': True,
            'complevel': 4, 
            'dtype': 'float32'
        },
        'time': {
            'units': f'seconds since {time_reference}',
            'calendar': 'gregorian',
            'dtype': 'float64'
        },
        'time_bnds': {
            'units': f'seconds since {time_reference}',
            'calendar': 'gregorian', 
            'dtype': 'float64'
        }
    }
    
    # Write to NetCDF file
    subset_ds.to_netcdf(
        output_file,
        format='NETCDF4',
        encoding=encoding,
        unlimited_dims=['time']
    )
    
    # Print summary information
    print(f"Created CF-compliant file: {output_file}")
    print(f"Time: {dt}")
    print(f"Grid size: {len(x_coords)} x {len(y_coords)}")
    print(f"Snow pixels: {np.sum(ds['bin_snow'].values)} / {len(x_coords) * len(y_coords)}")
    print(f"Longitude range: {lons.min():.2f} to {lons.max():.2f}")
    print(f"Latitude range: {lats.min():.2f} to {lats.max():.2f}")
    print(f"Projection: Lambert Conformal Conic (lat0=80.0, lon0=-34.0)")
    print(f"Grid spacing: {dx:.1f} m")
    print(f"CF Convention: {subset_ds.attrs['Conventions']}")
    print(f"UUID: {unique_id}")

# Process each time step
for time in date_range.time:
    date = datetime.datetime.strftime(pd.to_datetime(time.item()), "%Y-%m-%d")
    ims_dump = date_range.sel(time=time)
    date_formatted = date.replace("-", "")
    dump_subset_cf_compliant(ims_dump, os.path.join(out_path,f"ims_amsr2_{date_formatted}.nc"))
