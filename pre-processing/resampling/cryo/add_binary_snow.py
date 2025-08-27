#!/usr/bin/env python3
"""
Script to add a binary snow variable to NetCDF files and preserve time dimension.
Creates bin_snow = 1 where prob_snow >= 80, else 0.
Also copies time dimension and variable from original file if available.
"""

import sys
import numpy as np
import netCDF4 as nc
from pathlib import Path

def add_binary_snow_with_time(input_file, output_file=None, threshold=80., original_file=None):
    """
    Add binary snow variable to NetCDF file and preserve time dimension.
    
    Parameters:
    -----------
    input_file : str
        Path to input NetCDF file (regridded)
    output_file : str, optional
        Path to output NetCDF file. If None, creates based on input filename
    threshold : float, default 80.0
        Threshold for binary classification
    original_file : str, optional
        Path to original NetCDF file to extract time from
    """
    
    if output_file is None:
        # Create output filename by adding '_with_bin' before the extension
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_with_bin{input_path.suffix}"
    
    print(f"Processing: {input_file}")
    print(f"Output: {output_file}")
    print(f"Threshold: {threshold}")
    if original_file:
        print(f"Original file for time: {original_file}")
    
    # Read time information from original file if provided
    time_var_data = None
    time_attrs = {}
    time_dim_size = 1
    
    if original_file and Path(original_file).exists():
        try:
            with nc.Dataset(original_file, 'r') as orig:
                if 'time' in orig.variables:
                    time_var = orig.variables['time']
                    time_var_data = time_var[:]
                    time_attrs = {k: time_var.getncattr(k) for k in time_var.ncattrs()}
                    time_dim_size = len(time_var_data) if hasattr(time_var_data, '__len__') else 1
                    print(f"Found time variable with {time_dim_size} values")
        except Exception as e:
            print(f"Warning: Could not read time from original file: {e}")
    
    # Read the input file
    with nc.Dataset(input_file, 'r') as src:
        # Check if prob_snow exists
        if 'prob_snow' not in src.variables:
            raise ValueError("Variable 'prob_snow' not found in input file")
        
        # Create output file
        with nc.Dataset(output_file, 'w') as dst:
            # Copy global attributes
            dst.setncatts(src.__dict__)
            
            # Create time dimension if we have time data
            if time_var_data is not None:
                dst.createDimension('time', time_dim_size)
            
            # Copy other dimensions
            for name, dimension in src.dimensions.items():
                if name != 'time':  # Don't duplicate time dimension
                    dst.createDimension(
                        name, (len(dimension) if not dimension.isunlimited() else None)
                    )
            
            # Create time variable if we have time data
            if time_var_data is not None:
                time_out = dst.createVariable('time', time_var_data.dtype, ('time',))
                time_out.setncatts(time_attrs)
                time_out[:] = time_var_data
            
            # Copy all existing variables but modify their dimensions to include time
            for name, variable in src.variables.items():
                # Determine new dimensions
                if time_var_data is not None and name in ['prob_snow', 'classed_value']:
                    # Add time dimension to data variables
                    new_dims = ('time',) + variable.dimensions
                else:
                    new_dims = variable.dimensions
                
                # Create variable with same type and new dimensions
                var = dst.createVariable(
                    name, variable.datatype, new_dims,
                    fill_value=getattr(variable, '_FillValue', None)
                )
                
                # Copy variable attributes
                var.setncatts(variable.__dict__)
                
                # Copy data, adding time dimension if needed
                if time_var_data is not None and name in ['prob_snow', 'classed_value']:
                    # Add time dimension (assuming single time step)
                    var[0, :, :] = variable[:]
                else:
                    var[:] = variable[:]
            
            # Read prob_snow data
            prob_snow = src.variables['prob_snow'][:]
            
            # Determine dimensions for bin_snow
            if time_var_data is not None:
                bin_snow_dims = ('time', 'y', 'x')
            else:
                bin_snow_dims = ('y', 'x')
            
            # Create bin_snow variable
            bin_snow_var = dst.createVariable(
                'bin_snow', 'i1', bin_snow_dims,  # int8 type
                fill_value=-1  # Use -1 for missing data
            )
            
            # Set attributes for bin_snow
            bin_snow_var.long_name = "Binary snow cover flag"
            bin_snow_var.description = f"Binary flag: 1 where prob_snow >= {threshold}, 0 otherwise"
            bin_snow_var.units = "1"
            if 'grid_mapping' in src.variables['prob_snow'].ncattrs():
                bin_snow_var.grid_mapping = src.variables['prob_snow'].grid_mapping
            bin_snow_var.valid_range = np.array([0, 1], dtype='i1')
            
            # Calculate binary snow
            # Handle NaN values in prob_snow
            bin_snow_data = np.full_like(prob_snow, -1, dtype='i1')  # Initialize with fill value
            
            # Set valid data points
            valid_mask = ~np.isnan(prob_snow)
            bin_snow_data[valid_mask] = (prob_snow[valid_mask] >= threshold).astype('i1')
            
            # Write the data with appropriate dimensions
            if time_var_data is not None:
                bin_snow_var[0, :, :] = bin_snow_data
            else:
                bin_snow_var[:] = bin_snow_data
            
            print(f"Binary snow statistics:")
            valid_data = bin_snow_data[valid_mask]
            snow_pixels = np.sum(valid_data == 1)
            no_snow_pixels = np.sum(valid_data == 0)
            total_valid = len(valid_data)
            
            print(f"  Total valid pixels: {total_valid:,}")
            print(f"  Snow pixels (bin_snow=1): {snow_pixels:,} ({100*snow_pixels/total_valid:.1f}%)")
            print(f"  No-snow pixels (bin_snow=0): {no_snow_pixels:,} ({100*no_snow_pixels/total_valid:.1f}%)")
            print(f"  Missing data pixels: {np.sum(bin_snow_data == -1):,}")

    print(f"\nSuccessfully created: {output_file}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python add_binary_snow.py input_file.nc [output_file.nc] [threshold] [original_file.nc]")
        print("\nExamples:")
        print("  python add_binary_snow.py cryo_snow_regridded_20150908.nc")
        print("  python add_binary_snow.py input.nc output.nc")
        print("  python add_binary_snow.py input.nc output.nc 80.0")
        print("  python add_binary_snow.py regridded.nc output.nc 80.0 original.nc")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 80.0
    original_file = sys.argv[4] if len(sys.argv) > 4 else None
    
    try:
        add_binary_snow_with_time(input_file, output_file, threshold, original_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
