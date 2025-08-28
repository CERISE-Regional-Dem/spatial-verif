import xarray as xr
import numpy as np
import json
import datetime
import sys

def reformat_cryo_file(input_file, output_file):
    """Reformat cryo file to be CF-compliant and MET-compatible"""
    
    # Open the original cryo file
    cryo = xr.open_dataset(input_file)
    
    print(f"Processing: {input_file}")
    print(f"Variables in original file: {list(cryo.data_vars.keys())}")
    
    # Create new dataset with the same data but proper structure
    # Create completely new DataArrays and coordinates to avoid attribute conflicts
    new_cryo = xr.Dataset({
        'classed_value': (('time', 'y', 'x'), cryo.classed_value.values),
        'prob_snow': (('time', 'y', 'x'), cryo.prob_snow.values)
    }, coords={
        'time': (('time',), cryo.time.values),
        'y': (('y',), cryo.y.values), 
        'x': (('x',), cryo.x.values)
    })
    
    # Create binary snow variable: 1 if classed_value != 4, 0 otherwise
    bin_snow_data = np.where(cryo.classed_value.values != 4, 1, 0)
    new_cryo['bin_snow'] = (('time', 'y', 'x'), bin_snow_data)
    
    # Add lat/lon as data variables (not coordinates) for MET compatibility
    new_cryo['lat'] = (('y', 'x'), cryo.lat.values)
    new_cryo['lon'] = (('y', 'x'), cryo.lon.values)
    
    # Set proper coordinate attributes for MET compatibility
    new_cryo['x'].attrs = {
        'standard_name': 'projection_x_coordinate',
        'long_name': 'x coordinate of projection',
        'units': 'm',
        'axis': 'X'
    }
    
    new_cryo['y'].attrs = {
        'standard_name': 'projection_y_coordinate', 
        'long_name': 'y coordinate of projection',
        'units': 'm',
        'axis': 'Y'
    }
    
    # Handle time attributes correctly
    new_cryo['time'].attrs = {
        'long_name': 'time',
        'standard_name': 'time'
    }
    new_cryo['time'].encoding.update({
        'units': cryo.time.attrs.get('units', 'days since 2015-10-30 12:00:00'),
        'calendar': cryo.time.attrs.get('calendar', 'proleptic_gregorian')
    })
    
    # Set lat/lon attributes
    new_cryo['lat'].attrs = {
        'standard_name': 'latitude',
        'long_name': 'latitude',
        'units': 'degrees_north',
        'valid_min': -90.0,
        'valid_max': 90.0
    }
    
    new_cryo['lon'].attrs = {
        'standard_name': 'longitude', 
        'long_name': 'longitude',
        'units': 'degrees_east',
        'valid_min': -180.0,
        'valid_max': 180.0
    }
    
    # Parse projection info from original attributes
    proj_dict = json.loads(cryo.attrs['proj_dict'])
    
    # Create CF-compliant CRS variable
    crs_attrs = {
        'grid_mapping_name': 'lambert_azimuthal_equal_area',
        'latitude_of_projection_origin': float(proj_dict['lat_0']),
        'longitude_of_projection_origin': float(proj_dict['lon_0']),
        'false_easting': float(proj_dict['x_0']),
        'false_northing': float(proj_dict['y_0']),
        'semi_major_axis': 6378137.0,  # WGS84 semi-major axis
        'inverse_flattening': 298.257223563,  # WGS84 inverse flattening
        'proj4_params': f"+proj={proj_dict['proj']} +lat_0={proj_dict['lat_0']} +lon_0={proj_dict['lon_0']} +x_0={proj_dict['x_0']} +y_0={proj_dict['y_0']} +datum={proj_dict['datum']} +units={proj_dict['units']} +no_defs",
        'long_name': 'Coordinate reference system'
    }
    
    new_cryo['crs'] = xr.DataArray(0, attrs=crs_attrs)
    
    # Set data variable attributes
    new_cryo['classed_value'].attrs = {
        'long_name': 'Snow cover classification',
        'units': '1',
        'grid_mapping': 'crs',
        'coordinates': 'lat lon'
    }
    
    new_cryo['prob_snow'].attrs = {
        'long_name': 'Snow cover probability',
        'units': '1', 
        'grid_mapping': 'crs',
        'coordinates': 'lat lon'
    }
    
    # Set global attributes (CF-compliant)
    new_cryo.attrs = {
        'Conventions': 'CF-1.7',
        'title': 'Snow cover data (reformatted)',
        'institution': 'Original data provider',
        'source': 'Reformatted cryo snow cover data',
        'history': f'Reformatted on {datetime.datetime.now().strftime("%Y-%m-%d")} to be CF-1.7 and MET compliant. Original file: {input_file}',
        # Keep original projection info for reference
        'area_id': cryo.attrs['area_id'],
        'description': cryo.attrs['description'],
        'proj_id': cryo.attrs['proj_id'],
        'width': cryo.attrs['width'],
        'height': cryo.attrs['height'],
        'area_extent': cryo.attrs['area_extent'],
        'proj_dict': cryo.attrs['proj_dict']
    }
    
    # Write to netCDF file
    new_cryo.to_netcdf(output_file, format='NETCDF4', encoding={
        'classed_value': {'zlib': True, 'complevel': 4},
        'prob_snow': {'zlib': True, 'complevel': 4, '_FillValue': np.nan},
        'lat': {'zlib': True, 'complevel': 4},
        'lon': {'zlib': True, 'complevel': 4},
        'x': {'zlib': True, 'complevel': 4},
        'y': {'zlib': True, 'complevel': 4},
        'crs': {'dtype': 'int32'}
    })
    
    print(f"Created reformatted file: {output_file}")
    
    # Close original dataset
    cryo.close()

def main():
    """Main function to process command line arguments"""
    if len(sys.argv) != 3:
        print("Usage: python reformat_cryo.py <input_file> <output_file>")
        print("Example: python reformat_cryo.py /path/to/snowcover_daily_20151030.nc /path/to/snowcover_daily_20151030_reformatted.nc")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        reformat_cryo_file(input_file, output_file)
        print("SUCCESS: File reformatted successfully!")
    except Exception as e:
        print(f"ERROR: Failed to reformat file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()  
