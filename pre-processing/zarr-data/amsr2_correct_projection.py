import xarray as xr
import numpy as np
import pandas as pd
import sys
import os
from datetime import datetime, timezone
import pyproj
import pyresample
import uuid

def create_ims_projection_coords(nx, ny):
    """
    Create projection coordinates using the same IMS projection as ims_amsr2_compliant.py
    """
    # IMS projection parameters from ims_amsr2_compliant.py
    x_min, y_min, x_max, y_max = 537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063
    dx = (x_max - x_min) / nx  # Should be 2500m
    dy = (y_max - y_min) / ny  # Should be 2500m
    
    # Create coordinate arrays in projection space (meters) - cell centers
    x_coords = np.linspace(x_min + dx/2, x_max - dx/2, nx)
    y_coords = np.linspace(y_min + dy/2, y_max - dy/2, ny)
    
    return x_coords, y_coords, dx

def calculate_ims_lonlat_coords(x_coords, y_coords):
    """
    Calculate longitude/latitude coordinates using IMS projection
    Same as in ims_amsr2_compliant.py
    """
    # Define the IMS projection (exactly as in ims_amsr2_compliant.py)
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

def parse_time_from_filename(filename):
    """
    Extract time information from filename like SURFOUT.20180930_03h00.nc
    Returns datetime object
    """
    basename = os.path.basename(filename)
    # Extract the date and time part: 20180930_03h00
    time_str = basename.split('.')[1].replace('.nc', '')
    date_part, time_part = time_str.split('_')
    hour = time_part.replace('h00', '')
    
    # Create datetime object
    dt = datetime.strptime(f"{date_part}{hour.zfill(2)}", "%Y%m%d%H")
    return dt

def create_cf_compliant_snow_dataset(input_file, output_file=None, use_ims_projection=True):
    """
    Creates a CF-compliant NetCDF file extracting binary snow cover data 
    following CF conventions and model evaluation tool standards.
    
    Parameters:
    -----------
    input_file : str
        Path to input SURFEX NetCDF file
    output_file : str, optional
        Path to output NetCDF file
    use_ims_projection : bool, default True
        If True, uses IMS projection instead of original SURFEX projection
    """
    # Parse time from filename
    dt = parse_time_from_filename(input_file)
    print(f"Extracted time: {dt}")
    
    # Open the NetCDF file
    isba_analysis = xr.open_dataset(input_file)
    
    # Create the 'bin_snow' variable - binary snow cover based on depth threshold
    snow_depth_threshold = 0.01  # meters
    bin_snow = xr.where(isba_analysis["DSN_T_ISBA"] > snow_depth_threshold, 1, 0)
    
    if use_ims_projection:
        # Use IMS projection (same as ims_amsr2_compliant.py)
        ny, nx = isba_analysis['XX'].shape
        x_coords, y_coords, dx = create_ims_projection_coords(nx, ny)
        lons, lats = calculate_ims_lonlat_coords(x_coords, y_coords)
        
        # IMS projection parameters
        lat0, lon0 = 80.0, -34.0
        
        # Create projection variable for CF grid mapping (IMS version)
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
        
    else:
        # Original SURFEX projection
        lat0 = isba_analysis['LAT0'].item()
        lon0 = isba_analysis['LON0'].item()
        latc = isba_analysis["LATORI"].item()
        lonc = isba_analysis["LONORI"].item()
        ny, nx = isba_analysis['XX'].shape
        DX = isba_analysis["DX"]
        dx = DX[0][0].item()
        
        # Get area definition and longitude/latitude coordinates
        area_def, proj_obj = sfx2areadef(lat0, lon0, latc, lonc, nx, ny, dx=dx, get_proj=True)
        lons, lats = area_def.get_lonlats()
        
        # Grid coordinates (projection coordinates)
        x_coords = np.arange(nx) * dx - (nx-1) * dx / 2
        y_coords = np.arange(ny) * dx - (ny-1) * dx / 2
        
        # Create projection variable for CF grid mapping (original)
        proj_var = xr.DataArray(
            data=np.array([], dtype='c'),  # Empty array for grid mapping variable
            attrs={
                'grid_mapping_name': 'lambert_conformal_conic',
                'longitude_of_central_meridian': lon0,
                'latitude_of_projection_origin': lat0,
                'standard_parallel': [lat0, lat0],  # Using same latitude for both standard parallels
                'false_easting': 0.0,
                'false_northing': 0.0,
                'semi_major_axis': 6378137.0,  # WGS84 semi-major axis
                'inverse_flattening': 298.257223563,  # WGS84 inverse flattening
            }
        )
    
    # Define time reference for encoding
    time_reference = f"{dt.strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Create time bounds for CF compliance
    time_bounds = xr.DataArray(
        data=np.array([[dt, dt]]),  # Point measurement, so start and end are the same
        dims=['time', 'nv'],
        attrs={
            'long_name': 'time bounds'
        }
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
    
    # Grid coordinates (projection coordinates)
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
    
    # Binary snow cover variable with comprehensive CF attributes
    bin_snow_var = xr.DataArray(
        data=bin_snow.values[np.newaxis, :, :],  # Add time dimension
        dims=['time', 'y', 'x'],
        attrs={
            'long_name': 'Binary snow cover indicator',
            'standard_name': 'bin_snow',  # Note: This is not in CF standard names table
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
            'comment': f'Binary snow cover derived from snow depth with threshold {snow_depth_threshold} m. Value 1 indicates snow presence, 0 indicates no snow.',
            'ancillary_variables': 'snow_depth_threshold'
        }
    )
    
    # Add threshold as auxiliary variable
    threshold_var = xr.DataArray(
        data=snow_depth_threshold,
        attrs={
            'long_name': 'Snow depth threshold for binary classification',
            'units': 'm',
            'comment': 'Threshold used to determine binary snow cover classification'
        }
    )
    
    # Create the CF-compliant dataset
    ds = xr.Dataset(
        data_vars={
            'bin_snow': bin_snow_var,
            'lambert_conformal_conic': proj_var,
            'longitude': longitude_var,
            'latitude': latitude_var,
            'time_bnds': time_bounds,
            'snow_depth_threshold': threshold_var
        },
        coords={
            'time': time_coord,
            'x': x_coord,
            'y': y_coord,
            'nv': xr.DataArray([0, 1], dims=['nv'])  # Bounds dimension
        }
    )
    
    # Add comprehensive global attributes following CF and ACDD conventions
    creation_time = datetime.now(timezone.utc)
    unique_id = str(uuid.uuid4())
    
    ds.attrs = {
        # CF Convention requirements
        'Conventions': 'CF-1.8',
        
        # ACDD recommended global attributes
        'title': 'Binary Snow Cover Analysis from SURFEX Model Output',
        'summary': 'Binary snow cover classification derived from SURFEX land surface model snow depth output. Values indicate presence (1) or absence (0) of snow based on depth threshold.',
        'keywords': 'snow, snow cover, binary classification, land surface model, SURFEX, cryosphere',
        'keywords_vocabulary': 'GCMD Science Keywords',
        
        # Dataset identification
        'id': unique_id,
        'naming_authority': 'local',
        'creator_name': 'Automated Processing Script',
        'creator_type': 'person',
        'creator_institution': 'Not specified',
        'publisher_name': 'Not specified',
        'publisher_type': 'person',
        'publisher_institution': 'Not specified',
        
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
        'geospatial_lat_resolution': f'{abs(dx / 111000.0):.6f} degrees',  # Approximate conversion
        'geospatial_lon_resolution': f'{abs(dx / 111000.0):.6f} degrees',
        'geospatial_vertical_min': 0.0,
        'geospatial_vertical_max': 0.0,
        'geospatial_vertical_units': 'm',
        'geospatial_vertical_positive': 'up',
        
        # Processing and source information
        'source': f'SURFEX land surface model output file: {os.path.basename(input_file)}',
        'processing_level': 'Level 2',
        'product_version': '1.0',
        'references': 'https://www.umr-cnrm.fr/surfex/',
        'comment': f'Binary snow cover classification with threshold {snow_depth_threshold} m applied to snow depth data',
        'acknowledgment': 'SURFEX land surface model',
        
        # Technical metadata
        'date_created': creation_time.isoformat() + 'Z',
        'date_modified': creation_time.isoformat() + 'Z',
        'date_metadata_modified': creation_time.isoformat() + 'Z',
        'history': f'{creation_time.isoformat()}Z: Binary snow cover extracted from {os.path.basename(input_file)} using threshold {snow_depth_threshold} m',
        'institution': 'Local Processing',
        'program': 'Snow Cover Extraction Tool',
        'platform': 'SURFEX Land Surface Model',
        'instrument': 'Model',
        
        # File format and standards compliance
        'cdm_data_type': 'Grid',
        'standard_name_vocabulary': 'CF Standard Name Table v79',
        'license': 'Not specified - please check with data provider',
        
        # Grid information
        'grid_mapping_name': 'lambert_conformal_conic',
        'projection_lat0': lat0,
        'projection_lon0': lon0,
        'grid_spacing_m': dx,
        'grid_size_x': len(x_coords),
        'grid_size_y': len(y_coords),
        'bounding_box': [x_coords.min(), y_coords.min(), x_coords.max(), y_coords.max()],
        
        # ESMValTool and model evaluation compatibility
        'project': 'Local Analysis',
        'dataset': 'SURFEX',
        'mip': 'local',
        'realm': 'land',
        'frequency': 'fx',  # Fixed field
        'modeling_realm': 'land',
        'table_id': 'fx',
        'variable_id': 'bin_snow',
        'cf_standard_name': 'bin_snow',  # Custom standard name
        'cell_methods': 'time: point',
        'cell_measures': ''
    }
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}_bin_snow.nc"
    
    # Set encoding for NetCDF4 with compression and chunking
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
    
    # Save to NetCDF with CF compliance
    ds.to_netcdf(
        output_file,
        format='NETCDF4',
        encoding=encoding,
        unlimited_dims=['time']
    )
    
    print(f"CF-compliant dataset saved to: {output_file}")
    
    # Print summary information
    print(f"\nDataset summary:")
    print(f"Time: {dt}")
    print(f"Grid size: {len(x_coords)} x {len(y_coords)}")
    print(f"Snow pixels: {np.sum(bin_snow.values)} / {len(x_coords)*len(y_coords)}")
    print(f"Longitude range: {lons.min():.2f} to {lons.max():.2f}")
    print(f"Latitude range: {lats.min():.2f} to {lats.max():.2f}")
    print(f"Projection: Lambert Conformal Conic (lat0={lat0}, lon0={lon0})")
    print(f"Grid spacing: {dx:.1f} m")
    print(f"CF Convention: {ds.attrs['Conventions']}")
    print(f"UUID: {unique_id}")
    
    return ds

# Keep the rest of the functions unchanged (sfx2areadef, validate_cf_compliance, extract_to_csv)
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
    """
    proj_type = "lcc" if lat0 < 90 else "stere"
    proj_dict = {
        "proj": proj_type,
        "lat_0": lat0,
        "lon_0": lon0,
        "ellps": "WGS84",
        "no_defs": True,
        "units": "m",
    }
    if lat0 < 90:
        proj_dict["lat_1"] = lat0
        proj_dict["lat_2"] = lat0
    
    p = pyproj.Proj(proj_dict, preserve_units=False)
    center = p(lonc, latc, inverse=False)
    ll = (center[0] - dx*nx/2, center[1] - dx*ny/2)
    extent = ll + (ll[0] + nx*dx, ll[1] + ny*dx)
    area_def = pyresample.geometry.AreaDefinition("domain", "domain", proj_type, proj_dict, nx, ny, extent)
    
    if get_proj:
        return area_def, p
    return area_def

def validate_cf_compliance(dataset):
    """
    Basic validation checks for CF compliance
    """
    checks = []
    
    # Check required global attributes
    required_attrs = ['Conventions']
    for attr in required_attrs:
        if attr in dataset.attrs:
            checks.append(f"✓ Required global attribute '{attr}' present")
        else:
            checks.append(f"✗ Missing required global attribute '{attr}'")
    
    # Check coordinate variables
    for var_name, var in dataset.data_vars.items():
        if 'standard_name' in var.attrs:
            checks.append(f"✓ Variable '{var_name}' has standard_name")
        else:
            checks.append(f"! Variable '{var_name}' missing standard_name (recommended)")
            
        if 'units' in var.attrs:
            checks.append(f"✓ Variable '{var_name}' has units")
        else:
            checks.append(f"✗ Variable '{var_name}' missing units")
    
    print("\nCF Compliance Check:")
    for check in checks[:10]:  # Show first 10 checks
        print(f"  {check}")
    if len(checks) > 10:
        print(f"  ... and {len(checks)-10} more checks")
    
    return checks

def extract_to_csv(input_file, output_file=None, use_ims_projection=True):
    """
    Alternative function to extract data to CSV format with coordinates flattened.
    """
    # Get the extracted dataset
    ds = create_cf_compliant_snow_dataset(input_file, output_file=None, use_ims_projection=use_ims_projection)  # Don't save NetCDF yet
    
    # Flatten the 2D arrays
    time_flat = [ds.time.values[0]] * (ds.dims['x'] * ds.dims['y'])
    lon_flat = ds.longitude.values.flatten()
    lat_flat = ds.latitude.values.flatten() 
    snow_flat = ds.bin_snow.values[0].flatten()  # Remove time dimension
    
    # Create DataFrame
    df = pd.DataFrame({
        'time': time_flat,
        'longitude': lon_flat,
        'latitude': lat_flat,
        'bin_snow': snow_flat
    })
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}_bin_snow.csv"
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"CSV data saved to: {output_file}")
    
    return df

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <input_netcdf_file> [output_file] [--csv] [--validate] [--original-proj]")
        print("Options:")
        print("  --csv           Export to CSV format instead of NetCDF")
        print("  --validate      Run CF compliance validation checks")
        print("  --original-proj Use original SURFEX projection instead of IMS projection")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Check options
    csv_output = '--csv' in sys.argv
    validate = '--validate' in sys.argv
    use_ims_projection = '--original-proj' not in sys.argv  # Default to IMS projection
    
    # Get output file name
    #output_path = None
    for i, arg in enumerate(sys.argv[3:], 2):
        if arg not in ['--csv', '--validate', '--original-proj']:
            output_path = arg
            break
    
    # Extract the data
    if csv_output:
        extract_to_csv(input_path, output_path, use_ims_projection)
    else:
        ds = create_cf_compliant_snow_dataset(input_path, output_path, use_ims_projection)
        
        if validate:
            validate_cf_compliance(ds)
