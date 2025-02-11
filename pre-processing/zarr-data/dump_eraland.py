import xarray as xr
import numpy as np

import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime

import pandas as pd


eraland_analysis = xr.open_zarr("/ec/scratch/fab0/Projects/cerise/carra_snow_data/eraland.zarr/")
# Dimensions:     (time: 1583, y: 1000, x: 800)
#eraland_analysis["bin_snow"] = np.where(eraland_analysis["rsn"] != 0, (eraland_analysis["sd"] / eraland_analysis["rsn"] > 0.01).astype(int), np.nan)

date_range = eraland_analysis.sel(time=slice("2016-09-01","2016-09-30"))

def dump_subset(ds,output_file = 'binary_snow_classification.nc'):
    # Celect only the variables we want to keep
    subset_ds = ds[['bin_snow', 'y', 'x', 'crs']]
    
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
   eraland_dump = date_range.sel(time=time) 
   print(f"Dumping data for {date}")
   if len(eraland_dump["time"].dims) != 0:
       eraland_dump = eraland_dump.isel(time=0) #sometimes there are two times with the same value, not sure whY??
   eraland_dump["bin_snow"] = (
   ["y", "x"],  # specify dimensions
    np.where(eraland_dump["rsn"] != 0, (eraland_dump["sd"] / eraland_dump["rsn"] > 0.01).astype(int), np.nan)
   )
   #Create new coordinates based on dimension sizes
   new_x = np.arange(eraland_dump.dims['x'])  # Will create array from 0 to 799
   new_y = np.arange(eraland_dump.dims['y'])  # Will create array from 0 to 999
    
   # Assign new coordinates to the dataset
   #ims = ims.assign_coords(x=new_x, y=new_y)
   eraland_dump["x"] = np.arange(eraland_dump.dims['x'])
   eraland_dump["y"] = np.arange(eraland_dump.dims['y'])

   set_attrs(eraland_dump)
   date = date.replace("-","")
   dump_subset(eraland_dump,f"eraland_{date}.nc")
   #cerise_dump.to_netcdf(f"cerise_{date}.nc",format="NETCDF4")
   #cerise_dump["bin_snow"].to_netcdf(f"cerise_{date}.nc",format="NETCDF4")

