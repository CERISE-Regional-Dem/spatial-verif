import xarray as xr
import numpy as np

import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import sys

date_ini = str(sys.argv[1]) # "2016-09-01"
date_end = sys.argv[2]


#ims = xr.open_zarr("/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/ims.zarr")
ims = xr.open_zarr("/scratch/fab0/Projects/cerise/carra_snow_data/ims.zarr")

ims["bin_snow"]  = xr.where(ims["IMS_Surface_Values"] == 4, 1, 0)  

#Create new coordinates based on dimension sizes
new_x = np.arange(ims.dims['x'])  # Will create array from 0 to 799
new_y = np.arange(ims.dims['y'])  # Will create array from 0 to 999

# Assign new coordinates to the dataset
#ims = ims.assign_coords(x=new_x, y=new_y)
ims["x"] = np.arange(ims.dims['x'])
ims["y"] = np.arange(ims.dims['y'])


date_range = ims.sel(time=slice(date_ini,date_end))

def dump_subset(ds,output_file = 'binary_snow_classification.nc'):
    # Assuming ims_dump is your original dataset
    # First, select only the variables we want to keep
    subset_ds = ds[['bin_snow','time', 'y', 'x', 'crs']]
    
    # Add attributes for bin_snow if not already present
    subset_ds['bin_snow'].attrs.update({
        'standard_name': 'binary_snow_classification',
        'long_name': 'Binary classification of snow presence',
        'units': '1',  # dimensionless
        'valid_min': 0,
        'valid_max': 1,
        'grid_mapping': 'crs'  # Reference to the grid mapping variable
    })
    
    # Add proper CRS attributes
    subset_ds['crs'].attrs = {
        'grid_mapping_name': 'lambert_conformal_conic',
        'latitude_of_projection_origin': 80.0,
        'standard_parallel': [80.0, 80.0],
        'longitude_of_central_meridian': -34.0,
        'false_easting': 0.0,
        'false_northing': 0.0,
        'semi_major_axis': 6371000.0,
        'proj_string': '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0',
        'coordinates': 'patch stid time'
    }
    
    # Ensure global attributes are CF-1.7 compliant
    subset_ds.attrs.update({
        'Conventions': 'CF-1.7',
        'title': 'binary snow',
        'institution': 'DMI/Met Norway',
        'source': 'CERISE',
        'history': 'Modified on 2025-02-08 to be CF-1.7 compliant. Original: Created on 2025-02-07',
        'bounding_box': [537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063],
        'grid_size': [800, 1000],
        'projection': '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0'
    })
    
    # Write to netCDF file
    subset_ds.to_netcdf(output_file, format='NETCDF4', encoding={
        'bin_snow': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'crs': {'dtype': 'int64'}  # Ensure correct datatype for crs variable
    })
    
    # Print created file
    print(f"Created file: {output_file}")
    

def set_attrs(ds):
    # Step 1: Add CF-compliant global attributes
    ds.attrs["Conventions"] = "CF-1.7"
    ds.attrs["title"] = "binary snow"  # Add a descriptive title
    ds.attrs["institution"] = "DMI/Met Norway"  # Add your institution
    ds.attrs["source"] = "CERISE"  # Describe the data source
    ds.attrs["history"] = "Created on 2025-02-07"  # Add a history entry
    #ds.attrs["references"] = "References or links to documentation"
    
    
    # Step 2: Extract projection information from attributes
    proj_info = ds.attrs.get("projection", "")
    bounding_box = ds.attrs.get("bounding_box", [])
    grid_size = ds.attrs.get("grid_size", [])

    # Parse the PROJ string (manually extract parameters for CF compliance)
    # Example: '+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0'
    projection_params = {
    "grid_mapping_name": "lambert_conformal_conic",  # CF-compliant name for LCC
    "latitude_of_projection_origin": 80.0,  # +lat_0
    "standard_parallel": [80.0, 80.0],  # +lat_1 and +lat_2
    "longitude_of_central_meridian": -34.0,  # +lon_0
    "false_easting": 0.0,  # +x_0
    "false_northing": 0.0,  # +y_0
    "semi_major_axis": 6371000.0,  # +R
    "units": "m",  # +units
    "long_name": "CRS definition",
    "proj_string": proj_info,  # Store the original PROJ string for reference
    "bounding_box": bounding_box,  # Optional: Store bounding box for reference
    "grid_size": grid_size,  # Optional: Store grid size for reference
    }

    # Step 3: Add the projection information as a grid mapping variable
    ds["crs"] = xr.DataArray(0, attrs=projection_params)

    # Step 4: Link the grid mapping variable to data variables
    for var_name in ds.data_vars:
        ds[var_name].attrs["grid_mapping"] = "crs"  # Link to the projection variable

    # Step 3: Add CF-compliant variable attributes (example for one variable)
    for var_name in ds.data_vars:
        ds[var_name].attrs["units"] = "none"  # Replace with actual units
        ds[var_name].attrs["standard_name"] = "your_standard_name"  # Replace with CF standard name
        ds[var_name].attrs["long_name"] = "Descriptive name of the variable"

    ds["x"].attrs["units"] = "m"  # Units in meters
    ds["x"].attrs["standard_name"] = "projection_x_coordinate"  # CF standard name
    ds["x"].attrs["long_name"] = "x coordinate of projection"  # Descriptive name
    ds["x"].attrs["axis"] = "X"  # Axis designation

    ds["y"].attrs["units"] = "m"  # Units in meters
    ds["y"].attrs["standard_name"] = "projection_y_coordinate"  # CF standard name
    ds["y"].attrs["long_name"] = "y coordinate of projection"  # Descriptive name
    ds["y"].attrs["axis"] = "Y"  # Axis designation

for time in date_range.time:
   date = datetime.datetime.strftime(pd.to_datetime(time.item()),"%Y-%m-%d")
   ims_dump = date_range.sel(time=time) 
   set_attrs(ims_dump)
   date = date.replace("-","")
   dump_subset(ims_dump,f"ims_{date}.nc")
