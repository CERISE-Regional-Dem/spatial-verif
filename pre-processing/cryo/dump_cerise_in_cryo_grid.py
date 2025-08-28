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

# Get command line arguments
date_ini = str(sys.argv[1])  # "2016-09-01"
date_end = sys.argv[2]

# Load the analysis data
ana = xr.open_zarr(f"/scratch/fab0/Projects/cerise/carra_snow_data/ana_v2.zarr")

# Set up the input projection from ana dataset
proj_dict = ccrs.Projection(proj4_params=ana.projection).to_dict()
proj = pyproj.Proj(proj_dict)
input_def = pyresample.geometry.AreaDefinition(
    "model domain",
    "1", 
    "1",
    projection=proj_dict,
    width=ana.x.size,
    height=ana.y.size,
    area_extent=ana.bounding_box,
)

# Get the subset and date range
ana_subset = ana.mean(dim="member")
date_range = ana_subset.sel(time=slice(date_ini, date_end))

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

def dump_subset_cryo(subset_ds, cryo_attrs, output_file='binary_snow_classification_cryo.nc'):
    """Dump subset with cryo projection attributes"""
    # Select only the variables we want to keep
    subset_ds = subset_ds[['bin_snow', 'lat', 'lon']]
    
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
    
    # Add attributes for bin_snow
    subset_ds['bin_snow'].attrs.update({
        'standard_name': 'binary_snow_classification',
        'long_name': 'Binary classification of snow presence',
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
        'title': 'binary snow (cryo projection)',
        'institution': 'DMI/Met Norway',
        'source': 'CERISE resampled to cryo grid',
        'history': f'Modified on {datetime.datetime.now().strftime("%Y-%m-%d")} to cryo projection. Original: Created from CERISE analysis'
    })
    
    # Write to netCDF file
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4},
        'lat': {'zlib': True, 'complevel': 4},
        'lon': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
        'crs': {'dtype': 'int32'}
    })
    
    print(f"Created file: {output_file}")

def set_attrs_cryo(ds, cryo_attrs):
    """Set attributes for cryo projection dataset"""
    # Step 1: Add CF-compliant global attributes
    ds.attrs["Conventions"] = "CF-1.7"
    ds.attrs["title"] = "binary snow (cryo projection)"
    ds.attrs["institution"] = "DMI/Met Norway"
    ds.attrs["source"] = "CERISE resampled to cryo grid"
    ds.attrs["history"] = f"Created on {datetime.datetime.now().strftime('%Y-%m-%d')}"
    
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
        
    # Add standard attributes for data variables
    ds["bin_snow"].attrs.update({
        "units": "1",
        "standard_name": "binary_snow_classification", 
        "long_name": "Binary classification of snow presence",
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
    
    # Get the analysis data for this time
    ana_time = ana_subset.sel(time=time)
    
    # Resample the snow data to cryo grid
    ana_snow = resampler.resample(ana_time["hxa"].values[::-1])
    
    # Create binary snow classification
    bin_snow = np.where(ana_snow > 0.01, 1, 0)
    
    # Create new dataset with resampled data
    # For MET compatibility with Lambert Azimuthal Equal Area, we need 1D coordinate arrays
    # The lat/lon should be 2D coordinate arrays, not coordinate variables
    bin_snow_3d = bin_snow[np.newaxis, :, :]  # Add time dimension
    
    cryo_dump = xr.Dataset({
        'bin_snow': (('time', 'y', 'x'), bin_snow_3d)
    }, coords={
        'time': cryo.time,
        'y': cryo.y, 
        'x': cryo.x
    })
    
    # Add lat/lon as 2D data variables (not coordinates) for MET compatibility
    cryo_dump['lat'] = (('y', 'x'), cryo.lat.values)
    cryo_dump['lon'] = (('y', 'x'), cryo.lon.values)
    
    # Set proper coordinate attributes for MET compatibility
    cryo_dump['x'].attrs = {
        'standard_name': 'projection_x_coordinate',
        'long_name': 'x coordinate of projection',
        'units': 'm',
        'axis': 'X'
    }
    
    cryo_dump['y'].attrs = {
        'standard_name': 'projection_y_coordinate', 
        'long_name': 'y coordinate of projection',
        'units': 'm',
        'axis': 'Y'
    }
    
    # Set attributes
    set_attrs_cryo(cryo_dump, cryo.attrs)
    
    # Generate output filename
    date_filename = dt.strftime("%Y%m%d") 
    output_file = f"cerise_cryo_{date_filename}.nc"
    
    # Dump to file
    dump_subset_cryo(cryo_dump, cryo.attrs, output_file)
