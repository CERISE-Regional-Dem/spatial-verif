#!/usr/bin/env python
"""
Script to make CRYO files CF compliant and add bin_snow variable.
CF compliance requirements for MET grid_stat:
- Grid mapping variable with projection information
- Proper coordinate attributes on all data variables
- Standard names and units on all coordinate variables
"""

import netCDF4 as nc
import numpy as np
from datetime import datetime
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]
#input_file = '/media/cap/extra_work/CERISE/CARRA_Land_Pv2_stream_2015/snowcover_daily_20151015.nc'
#output_file = '/media/cap/extra_work/CERISE/CARRA_Land_Pv2_stream_2015/snowcover_daily_20151015_cf_compliant.nc'

print(f"Reading input file: {input_file}")
with nc.Dataset(input_file, 'r') as src:
    print(f"Creating output file: {output_file}")
    with nc.Dataset(output_file, 'w', format='NETCDF4') as dst:
        
        for name, dimension in src.dimensions.items():
            dst.createDimension(name, len(dimension) if not dimension.isunlimited() else None)
        
        crs_var = dst.createVariable('crs', 'i4')
        crs_var.grid_mapping_name = 'lambert_azimuthal_equal_area'
        crs_var.longitude_of_projection_origin = 0.0
        crs_var.latitude_of_projection_origin = 90.0
        crs_var.false_easting = 0.0
        crs_var.false_northing = 0.0
        crs_var.semi_major_axis = 6378137.0
        crs_var.semi_minor_axis = 6356752.314245
        crs_var.inverse_flattening = 298.257223563
        crs_var.proj4_string = '+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs'
        
        for name, variable in src.variables.items():
            dst.createVariable(name, variable.datatype, variable.dimensions, 
                             zlib=True, complevel=4)
            
            dst[name].setncatts({k: variable.getncattr(k) for k in variable.ncattrs()})
            dst[name][:] = variable[:]
        
        if 'time' in dst.variables:
            time_var = dst['time']
            time_var.units = 'seconds since 1970-01-01 00:00:00'
            time_var.calendar = 'gregorian'
            time_var.standard_name = 'time'
            time_var.long_name = 'time'
            time_var.axis = 'T'
        
        if 'x' in dst.variables:
            x_var = dst['x']
            x_var.standard_name = 'projection_x_coordinate'
            x_var.long_name = 'x coordinate of projection'
            x_var.units = 'm'
            x_var.axis = 'X'
        
        if 'y' in dst.variables:
            y_var = dst['y']
            y_var.standard_name = 'projection_y_coordinate'
            y_var.long_name = 'y coordinate of projection'
            y_var.units = 'm'
            y_var.axis = 'Y'
        
        if 'lat' in dst.variables:
            lat_var = dst['lat']
            lat_var.standard_name = 'latitude'
            lat_var.long_name = 'latitude'
            lat_var.units = 'degrees_north'
        
        if 'lon' in dst.variables:
            lon_var = dst['lon']
            lon_var.standard_name = 'longitude'
            lon_var.long_name = 'longitude'
            lon_var.units = 'degrees_east'
        
        for var_name in ['classed_value', 'prob_snow']:
            if var_name in dst.variables:
                var = dst[var_name]
                var.coordinates = 'lat lon'
                var.grid_mapping = 'crs'
                if 'standard_name' not in var.ncattrs():
                    if var_name == 'prob_snow':
                        var.standard_name = 'surface_snow_area_fraction'
                        var.long_name = 'Probability of snow cover'
                        var.units = '%'
                    elif var_name == 'classed_value':
                        var.long_name = 'Classified snow cover value'
                        var.units = '1'
        
        if 'prob_snow' in src.variables:
            prob_snow_data = src['prob_snow'][:]
            
            bin_snow_var = dst.createVariable('bin_snow', 'i1', src['prob_snow'].dimensions,
                                             zlib=True, complevel=4, fill_value=-1)
            
            bin_snow_var.long_name = 'Binary snow cover flag'
            bin_snow_var.standard_name = 'surface_snow_binary_mask'
            bin_snow_var.units = '1'
            bin_snow_var.valid_range = np.array([0, 1], dtype='i1')
            bin_snow_var.flag_values = np.array([0, 1], dtype='i1')
            bin_snow_var.flag_meanings = 'no_snow snow'
            bin_snow_var.description = 'Binary snow cover: 1 if prob_snow >= 80%, 0 otherwise'
            bin_snow_var.coordinates = 'lat lon'
            bin_snow_var.grid_mapping = 'crs'
            
            bin_snow_data = np.where(prob_snow_data >= 80, 1, 0).astype('i1')
            
            if hasattr(prob_snow_data, 'mask'):
                bin_snow_data = np.ma.masked_where(prob_snow_data.mask, bin_snow_data)
            
            bin_snow_var[:] = bin_snow_data
            
            print(f"Created bin_snow variable: {np.sum(bin_snow_data == 1)} snow pixels, {np.sum(bin_snow_data == 0)} no-snow pixels")
        
        dst.setncattr('Conventions', 'CF-1.8')
        dst.setncattr('title', 'CARRA Land Pv2 Daily Snow Cover')
        dst.setncattr('institution', 'CERISE')
        dst.setncattr('source', 'CARRA Land Pv2')
        dst.setncattr('history', f'{datetime.now().isoformat()}: Made CF compliant and added bin_snow variable')
        
        for attr in src.ncattrs():
            if attr not in dst.ncattrs():
                dst.setncattr(attr, src.getncattr(attr))

print(f"Successfully created CF-compliant file: {output_file}")
print("\nCF compliance features added:")
print("- Grid mapping variable (crs) with Lambert Azimuthal Equal Area projection")
print("- Coordinate attributes (lat lon) on all data variables")
print("- grid_mapping attribute on all data variables")
print("- Standard names and units on all coordinate variables")
print("- Axis attributes on x, y, time dimensions")
