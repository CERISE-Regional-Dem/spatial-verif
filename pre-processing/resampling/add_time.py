# Expand the coordinates of the file dumped by gdal with time
import numpy as np
import xarray as xr
import sys

# Open the file where the time coordinate is stored
#time_file = "ims2015121_1km_v1.3.nc"
#time_file = "ims2016131_1km_v1.3.nc"
#time_file = "ims_20160501_1km_v1.3.nc"

time_file = sys.argv[1]
snow_file = sys.argv[2]
output_file = sys.argv[3]
time_ds = xr.open_dataset(time_file)

# Extract the time coordinate
time_coord = time_ds['time']

# Open the file where snow_cover is stored
#snow_file = "regridded_output_CE.nc"  # Replace with your actual file name


#snow_file = "ims_20160501_latlon_NO-AR-CW.nc" # "ims2016131_latlon_NO-AR-CE.nc"  # Replace with your actual file name
snow_ds = xr.open_dataset(snow_file)
snow_ds = snow_ds.rename({"Band1": "snow_cover"})  
nx, ny = len(snow_ds.lon), len(snow_ds.lat)

# Define the new variable bin_snow
bin_snow = xr.where(snow_ds.snow_cover == 4, 1, 0).astype(np.int8)

# Add the time dimension to the variables
# Expand dimensions to include time
snow_ds = snow_ds.expand_dims(dim={'time': time_coord})
bin_snow = bin_snow.expand_dims(dim={'time': time_coord})

snow_ds = snow_ds.assign_coords(time=time_coord)

# Add the new variable bin_snow to the dataset
snow_ds['bin_snow'] = bin_snow
snow_ds["time"] = time_coord

# Save the updated dataset to a new NetCDF file
#output_file = snow_file.split(".nc")[0]+"_wtime.nc"

snow_ds.attrs.update({
        'nx': nx,
        'ny': ny,
        'grid_description': f'{nx}x{ny} regular lat-lon grid'
    })

snow_ds.to_netcdf(output_file)


