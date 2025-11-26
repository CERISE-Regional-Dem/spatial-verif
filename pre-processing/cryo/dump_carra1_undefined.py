import xarray as xr
import numpy as np
import json
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys
from pyresample.bilinear import NumpyBilinearResampler

# Define fill value
FILL_VALUE = np.nan

# Get command line arguments
date_ini = str(sys.argv[1])  # "2016-09-01"
date_end = sys.argv[2]

# Load the CARRA1 data
carra1_analysis = xr.open_zarr("/ec/scratch/fab0/Projects/cerise/carra_snow_data/carrasnow_v2.zarr")

# Set up the input projection from CARRA1 dataset
# Using the projection information from the dump_carra1.py script
proj_string = '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0'
proj = pyproj.Proj(proj_string)

# Get bounding box and grid size from CARRA1 attributes
bounding_box = [537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063]
grid_size = [800, 1000]  # [width, height]

input_def = pyresample.geometry.AreaDefinition(
    "carra1_domain",
    "CARRA1 Lambert Conformal Conic", 
    "carra1_lcc",
    projection=proj_string,
    width=grid_size[0],  # 800
    height=grid_size[1],  # 1000
    area_extent=bounding_box,
)

# Get the subset and date range
date_range = carra1_analysis.sel(time=slice(date_ini, date_end))

def setup_cryo_projection(dt):
    """Setup the cryo projection for a given datetime"""
    cryo = xr.open_dataset(f"/scratch/fab0/Projects/cerise/carra_snow_data/cryo/snowcover_daily_{dt.strftime('%Y%m%d')}.nc")
    
    cryo_def = pyresample.geometry.AreaDefinition(
        area_id=cryo.attrs['area_id'],
        description=cryo.attrs['description'],
        proj_id=cryo.attrs['proj_id'],
        projection=json.loads(cryo.attrs['proj_dict']),
        width=int(cryo.attrs['width']),
        height=int(cryo.attrs['height']),
        area_extent=tuple(map(float, cryo.attrs['area_extent'].split(',')))
    )
    return cryo, cryo_def

def apply_latitude_filter(data, lat_values):
    """Apply latitude filter: set values to fill value where lat >= 70 degrees"""
    print("Applying latitude filter: setting values to fill value where lat >= 70 degrees")
    lat_mask = lat_values >= 70.0
    print(f"Number of grid points with lat >= 70: {np.sum(lat_mask)}")
    
    # Convert data to float to allow NaN values
    data = data.astype(float)
    
    # Apply mask to data
    # If data is 3D (time, y, x), apply mask to all time steps
    if len(data.shape) == 3:
        for t in range(data.shape[0]):
            data[t][lat_mask] = FILL_VALUE
    # If data is 2D (y, x), apply mask directly
    elif len(data.shape) == 2:
        data[lat_mask] = FILL_VALUE
    
    return data

def dump_subset_cryo(subset_ds, cryo_attrs, output_file='binary_snow_classification_cryo.nc'):
    """Dump subset with cryo projection attributes"""
    # Select only the variables we want to keep
    subset_ds = subset_ds[['bin_snow', 'lat', 'lon']]
    
    # Clear any existing encoding and attributes to avoid conflicts
    for var_name in ['bin_snow']:
        if var_name in subset_ds.data_vars:
            subset_ds[var_name].encoding = {}
            subset_ds[var_name].attrs = {}
    
    # Ensure coordinate variables have proper standard names for MET compatibility
    if 'x' in subset_ds.coords:
        subset_ds['x'].attrs = {
            'standard_name': 'projection_x_coordinate',
            'long_name': 'x coordinate of projection', 
            'units': 'm',
            'axis': 'X'
        }
    
    if 'y' in subset_ds.coords:
        subset_ds['y'].attrs = {
            'standard_name': 'projection_y_coordinate',
            'long_name': 'y coordinate of projection',
            'units': 'm', 
            'axis': 'Y'
        }
    
    # Add CF-1.7 compliant attributes for lat/lon (as data variables, not coordinates)
    subset_ds['lat'].attrs = {
        'standard_name': 'latitude',
        'long_name': 'latitude',
        'units': 'degrees_north',
        'valid_min': -90.0,
        'valid_max': 90.0
    }
    
    subset_ds['lon'].attrs = {
        'standard_name': 'longitude', 
        'long_name': 'longitude',
        'units': 'degrees_east',
        'valid_min': -180.0,
        'valid_max': 180.0
    }
    
    # Add attributes for bin_snow (without _FillValue)
    subset_ds['bin_snow'].attrs.update({
        'standard_name': 'binary_snow_classification',
        'long_name': 'Binary classification of snow presence (CARRA1)',
        'units': '1',  # dimensionless
        'valid_min': 0,
        'valid_max': 1,
        'grid_mapping': 'crs',
        'coordinates': 'lat lon'
    })
    
    # Extract projection info from cryo attributes
    proj_dict = json.loads(cryo_attrs['proj_dict'])
    
    # Add proper CRS attributes based on cryo projection (Lambert Azimuthal Equal Area)
    crs_attrs = {
        'grid_mapping_name': 'lambert_azimuthal_equal_area',
        'latitude_of_projection_origin': float(proj_dict['lat_0']),  # lat_0
        'longitude_of_projection_origin': float(proj_dict['lon_0']),  # lon_0
        'false_easting': float(proj_dict['x_0']),  # x_0
        'false_northing': float(proj_dict['y_0']),  # y_0
        'semi_major_axis': 6378137.0,  # WGS84 semi-major axis
        'inverse_flattening': 298.257223563,  # WGS84 inverse flattening
        'proj4_params': f"+proj={proj_dict['proj']} +lat_0={proj_dict['lat_0']} +lon_0={proj_dict['lon_0']} +x_0={proj_dict['x_0']} +y_0={proj_dict['y_0']} +datum={proj_dict['datum']} +units={proj_dict['units']} +no_defs",
        'long_name': 'Coordinate reference system'
    }
    
    # Add the CRS variable
    subset_ds['crs'] = xr.DataArray(0, attrs=crs_attrs)
    
    # Ensure global attributes are CF-1.7 compliant
    subset_ds.attrs.update({
        'Conventions': 'CF-1.7',
        'title': 'binary snow CARRA1 (cryo projection)',
        'institution': 'DMI/Met Norway',
        'source': 'CARRA1 resampled to cryo grid',
        'history': f'Modified on {datetime.datetime.now().strftime("%Y-%m-%d")} to cryo projection. Latitude filter applied: values set to fill value where lat >= 70 degrees. Original: Created from CARRA1 analysis'
    })
    
    # Write to netCDF file with _FillValue in encoding only
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4, '_FillValue': FILL_VALUE},
        'lat': {'zlib': True, 'complevel': 4},
        'lon': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
        'crs': {'dtype': 'int32'}
    })
    
    print(f"Created file: {output_file}")

def set_attrs_cryo(ds, cryo_attrs):
    """Set attributes for cryo projection dataset"""
    # Clear any existing encoding and attributes for data variables to avoid conflicts
    for var_name in ds.data_vars:
        if var_name not in ['lat', 'lon', 'crs']:  # Don't clear lat/lon/crs attrs
            ds[var_name].encoding = {}
            ds[var_name].attrs = {}
    
    # Step 1: Add CF-compliant global attributes
    ds.attrs["Conventions"] = "CF-1.7"
    ds.attrs["title"] = "binary snow CARRA1 (cryo projection)"
    ds.attrs["institution"] = "DMI/Met Norway"
    ds.attrs["source"] = "CARRA1 resampled to cryo grid"
    ds.attrs["history"] = f"Created on {datetime.datetime.now().strftime('%Y-%m-%d')}. Latitude filter applied: values set to fill value where lat >= 70 degrees."
    
    # Parse projection info
    proj_dict = json.loads(cryo_attrs['proj_dict'])
    
    # Create CRS variable with Lambert Azimuthal Equal Area projection parameters
    crs_attrs = {
        "grid_mapping_name": "lambert_azimuthal_equal_area",
        "latitude_of_projection_origin": float(proj_dict['lat_0']),  # lat_0
        "longitude_of_projection_origin": float(proj_dict['lon_0']),  # lon_0
        "false_easting": float(proj_dict['x_0']),  # x_0
        "false_northing": float(proj_dict['y_0']),  # y_0
        "semi_major_axis": 6378137.0,  # WGS84 semi-major axis
        "inverse_flattening": 298.257223563,  # WGS84 inverse flattening
        "long_name": "Coordinate reference system",
        "proj4_params": f"+proj={proj_dict['proj']} +lat_0={proj_dict['lat_0']} +lon_0={proj_dict['lon_0']} +x_0={proj_dict['x_0']} +y_0={proj_dict['y_0']} +datum={proj_dict['datum']} +units={proj_dict['units']} +no_defs",
    }
    
    # Add the projection information as a grid mapping variable
    ds["crs"] = xr.DataArray(0, attrs=crs_attrs)
    
    # Link the grid mapping variable to data variables
    for var_name in ds.data_vars:
        if var_name not in ['crs', 'lat', 'lon']:  # Don't add grid_mapping to lat/lon or crs itself
            ds[var_name].attrs["grid_mapping"] = "crs"
        
    # Add standard attributes for data variables (without _FillValue)
    ds["bin_snow"].attrs.update({
        "units": "1",
        "standard_name": "binary_snow_classification", 
        "long_name": "Binary classification of snow presence (CARRA1)",
        "coordinates": "lat lon"
    })
    
    # Add coordinate attributes for lat/lon (as data variables, not coordinates)
    ds["lat"].attrs.update({
        "standard_name": "latitude",
        "long_name": "latitude",
        "units": "degrees_north"
    })
    
    ds["lon"].attrs.update({
        "standard_name": "longitude",
        "long_name": "longitude", 
        "units": "degrees_east"
    })
    
    # Add coordinate attributes for x/y (projection coordinates)
    if 'y' in ds.coords:
        ds["y"].attrs.update({
            "units": "m",
            "standard_name": "projection_y_coordinate",
            "long_name": "y coordinate of projection",
            "axis": "Y"
        })
    
    if 'x' in ds.coords:
        ds["x"].attrs.update({
            "units": "m",
            "standard_name": "projection_x_coordinate", 
            "long_name": "x coordinate of projection",
            "axis": "X"
        })

# Process each time step
for time in date_range.time:
    dt = pd.to_datetime(time.item())
    date_str = dt.strftime("%Y-%m-%d")
    
    # Setup cryo projection for this date
    cryo, cryo_def = setup_cryo_projection(dt)
    
    # Setup resampler
    resampler = NumpyBilinearResampler(input_def, cryo_def, 5000)
    
    # Get the CARRA1 data for this time
    carra1_time = date_range.sel(time=time)
    
    # Create binary snow classification using the same logic as dump_carra1.py
    # bin_snow = where(rsn != 0, (sd / rsn > 0.01).astype(int), np.nan)
    bin_snow_input = np.where(carra1_time["rsn"] != 0, 
                              (carra1_time["sd"] / carra1_time["rsn"] > 0.01).astype(int), 
                              np.nan)
    
    # Resample the binary snow data to cryo grid
    # Note: We need to flip the y-axis for proper resampling (similar to CERISE script)
    bin_snow_resampled = resampler.resample(bin_snow_input[::-1])
    
    # Handle NaN values after resampling - convert to 0 where appropriate
    bin_snow_final = np.where(np.isnan(bin_snow_resampled), 0, bin_snow_resampled).astype(int)
    
    # APPLY LATITUDE FILTER BEFORE CREATING DATASET
    # Apply the latitude filter to the resampled data
    bin_snow_filtered = apply_latitude_filter(bin_snow_final.copy(), cryo.lat.values)
    
    # Create new dataset with filtered resampled data
    # For MET compatibility with Lambert Azimuthal Equal Area, we need 1D coordinate arrays
    # The lat/lon should be 2D coordinate arrays, not coordinate variables
    bin_snow_3d = bin_snow_filtered[np.newaxis, :, :]  # Add time dimension
    
    carra1_cryo_dump = xr.Dataset({
        'bin_snow': (('time', 'y', 'x'), bin_snow_3d)
    }, coords={
        'time': cryo.time,
        'y': cryo.y, 
        'x': cryo.x
    })
    
    # Add lat/lon as 2D data variables (not coordinates) for MET compatibility
    carra1_cryo_dump['lat'] = (('y', 'x'), cryo.lat.values)
    carra1_cryo_dump['lon'] = (('y', 'x'), cryo.lon.values)
    
    # Set proper coordinate attributes for MET compatibility
    carra1_cryo_dump['x'].attrs = {
        'standard_name': 'projection_x_coordinate',
        'long_name': 'x coordinate of projection',
        'units': 'm',
        'axis': 'X'
    }
    
    carra1_cryo_dump['y'].attrs = {
        'standard_name': 'projection_y_coordinate', 
        'long_name': 'y coordinate of projection',
        'units': 'm',
        'axis': 'Y'
    }
    
    # Set attributes
    set_attrs_cryo(carra1_cryo_dump, cryo.attrs)
    
    # Generate output filename
    date_filename = dt.strftime("%Y%m%d") 
    output_file = f"carra1_cryo_{date_filename}.nc"
    
    # Dump to file
    dump_subset_cryo(carra1_cryo_dump, cryo.attrs, output_file)
