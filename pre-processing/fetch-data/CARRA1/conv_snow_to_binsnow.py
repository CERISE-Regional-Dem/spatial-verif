import xarray as xr
import cfgrib
import numpy as np
from datetime import datetime
import sys

grib_file = sys.argv[1]
nc_file_save = sys.argv[2]

#grib_file = "carra1_snow_20160510_NO-AR-CE_reg.grib2"
#nc_file_save = 'bin_snow_carra1_20160510_NO-AR-CE_reg.nc'

# Read the GRIB2 file for each variable separately
ds_sd = xr.open_dataset(grib_file,
                        engine='cfgrib',
                        filter_by_keys={'shortName': 'sd'})

ds_rsn = xr.open_dataset(grib_file,
                         engine='cfgrib',
                         filter_by_keys={'shortName': 'rsn'})

# Print original projection information for debugging
print("Original dataset projection info:")
for var in ds_sd.variables:
    if 'grid_mapping' in ds_sd[var].attrs:
        print(f"Grid mapping from {var}:", ds_sd[var].attrs['grid_mapping'])
        grid_var = ds_sd[ds_sd[var].attrs['grid_mapping']]
        print("Grid variable attributes:", grid_var.attrs)

# Get projection information
grid_mapping_name = None
grid_mapping_attrs = {}

# Look for grid mapping in variables
for var in ds_sd.variables:
    if 'grid_mapping' in ds_sd[var].attrs:
        grid_mapping_name = ds_sd[var].attrs['grid_mapping']
        grid_mapping_attrs = ds_sd[grid_mapping_name].attrs
        break

# Calculate bin_snow as sd/rsn with handling for division by zero
#bin_snow = np.where(ds_rsn.rsn != 0, ds_sd.sd / ds_rsn.rsn, np.nan)
bin_snow = np.where(ds_rsn.rsn != 0, (ds_sd.sd / ds_rsn.rsn > 0.01).astype(int), np.nan)

# Create a new dataset with the calculated variable
new_ds = xr.Dataset({
    'bin_snow': (['latitude', 'longitude'], bin_snow),
}, coords={
    'latitude': ds_sd.latitude,
    'longitude': ds_sd.longitude,
})

# Copy the time coordinate from the original dataset
if 'time' in ds_sd.coords:
    new_ds.coords['time'] = ds_sd.time

# Add projection information
if grid_mapping_name is not None:
    # Add the grid mapping variable
    new_ds[grid_mapping_name] = xr.DataArray(attrs=grid_mapping_attrs)
    # Add grid mapping attribute to the data variable
    new_ds.bin_snow.attrs['grid_mapping'] = grid_mapping_name

# Copy relevant global attributes from original dataset
for attr in ds_sd.attrs:
    new_ds.attrs[attr] = ds_sd.attrs[attr]

# Set attributes for the new variable
new_ds.bin_snow.attrs.update({
    'units': 'None',
    'long_name': 'Binary Snow Ratio',
    'standard_name': 'binary_snow_ratio'
})

# Copy all coordinate reference system information
if hasattr(ds_sd, 'crs'):
    new_ds['crs'] = ds_sd.crs
if 'crs' in ds_sd.variables:
    new_ds['crs'] = ds_sd['crs']

# Print information about the new dataset
print("\nNew dataset information:")
print(new_ds)
print("\nNew dataset attributes:")
for var in new_ds.variables:
    print(f"\nVariable: {var}")
    print("Attributes:", new_ds[var].attrs)

# Save to a new GRIB2 file
# First save as netCDF with all metadata
encoding = {
    'bin_snow': {
        'zlib': True,
        'complevel': 5
    }
}

# Add encoding for coordinates if needed
for coord in new_ds.coords:
    encoding[coord] = {'zlib': True, 'complevel': 5}

new_ds.to_netcdf(nc_file_save, encoding=encoding)
