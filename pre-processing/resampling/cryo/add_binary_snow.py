#!/usr/bin/env python3
"""
Script to add a binary snow variable to NetCDF files and preserve time dimension.
Creates bin_snow = 1 where prob_snow >= 80.0, else 0.
Also copies time dimension and variable from original file if available.
"""

import sys
import numpy as np
import netCDF4 as nc
from pathlib import Path

def add_binary_snow_with_time(input_file, output_file=None, threshold=80.0, original_file=None,classed_file=None):
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
    if classed_file:
        print(f"Regridded classed value file: {classed_file}")
    
    # Read classed_value data from regridded file if provided
    classed_data = None
    if classed_file and Path(classed_file).exists():
        try:
            with nc.Dataset(classed_file, 'r') as classed_nc:
                if 'classed_value' in classed_nc.variables:
                    classed_data = classed_nc.variables['classed_value'][:]
                    print(f"Found classed_value with shape: {classed_data.shape}")
                    print(f"Classed_value unique values: {np.unique(classed_data[~np.isnan(classed_data)])}")
                else:
                    print("Warning: classed_value variable not found in regridded classed file")
        except Exception as e:
            print(f"Warning: Could not read classed_value from regridded file: {e}")
    else:
        print("Warning: Classed file not provided or does not exist")
    
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
                'bin_snow', 'i2', bin_snow_dims,  # int16 type to accommodate -9999
                fill_value=-9999  # Use -9999 for fill value as requested
            )
            
            # Set attributes for bin_snow
            bin_snow_var.long_name = "Binary snow cover flag"
            if classed_data is not None:
                bin_snow_var.description = f"Binary flag: 1 where prob_snow >= {threshold} AND classed_value != 4, -9999 where classed_value == 4, 0 otherwise"
            else:
                bin_snow_var.description = f"Binary flag: 1 where prob_snow >= {threshold}, 0 otherwise"
            bin_snow_var.units = "1"
            if 'grid_mapping' in src.variables['prob_snow'].ncattrs():
                bin_snow_var.grid_mapping = src.variables['prob_snow'].grid_mapping
            bin_snow_var.valid_range = np.array([0, 1], dtype='i2')
            
            # Calculate binary snow
            # Initialize with fill value
            bin_snow_data = np.full_like(prob_snow, -9999, dtype='i2')
            
            if classed_data is not None:
                # Use classed_value for masking
                # Set to fill value where classed_value == 4
                fill_mask = (classed_data == 4)
                
                # Set valid data where classed_value != 4 and prob_snow is not NaN
                valid_mask = (~np.isnan(prob_snow)) & (~fill_mask)
                
                # Set binary snow where conditions are met
                snow_condition = (prob_snow >= threshold) & valid_mask
                no_snow_condition = (prob_snow < threshold) & valid_mask
                
                bin_snow_data[snow_condition] = 1
                bin_snow_data[no_snow_condition] = 0
                # Fill values remain as -9999 where classed_value == 4
                
                print(f"Classed value masking statistics:")
                print(f"  Pixels where classed_value == 4 (fill): {np.sum(fill_mask):,}")
                print(f"  Valid pixels (classed_value != 4): {np.sum(valid_mask):,}")
                
            else:
                # Original behavior when no classed_value file is provided
                valid_mask = ~np.isnan(prob_snow)
                bin_snow_data[valid_mask & (prob_snow >= threshold)] = 1
                bin_snow_data[valid_mask & (prob_snow < threshold)] = 0
            
            # Write the data with appropriate dimensions
            if time_var_data is not None:
                bin_snow_var[0, :, :] = bin_snow_data
            else:
                bin_snow_var[:] = bin_snow_data
            
            print(f"Binary snow statistics:")
            # Calculate statistics only for non-fill values
            non_fill_mask = (bin_snow_data != -9999)
            if np.any(non_fill_mask):
                valid_data = bin_snow_data[non_fill_mask]
                snow_pixels = np.sum(valid_data == 1)
                no_snow_pixels = np.sum(valid_data == 0)
                total_valid = len(valid_data)
                
                print(f"  Total valid pixels: {total_valid:,}")
                print(f"  Snow pixels (bin_snow=1): {snow_pixels:,} ({100*snow_pixels/total_valid:.1f}%)")
                print(f"  No-snow pixels (bin_snow=0): {no_snow_pixels:,} ({100*no_snow_pixels/total_valid:.1f}%)")
            print(f"  Fill value pixels (bin_snow=-9999): {np.sum(bin_snow_data == -9999):,}")

    print(f"\nSuccessfully created: {output_file}")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python add_binary_snow.py input_file.nc [output_file.nc] [threshold] [original_file.nc] [classed_file.nc]")
        print("\nExamples:")
        print("  python add_binary_snow.py cryo_snow_regridded_20150908.nc")
        print("  python add_binary_snow.py input.nc output.nc")
        print("  python add_binary_snow.py input.nc output.nc 80.0")
        print("  python add_binary_snow.py regridded.nc output.nc 80.0 original.nc classed_data_file.nc")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 80.0
    original_file = sys.argv[4] if len(sys.argv) > 4 else None
    classed_file = sys.argv[5] if len(sys.argv) > 5 else None
    
    try:
        add_binary_snow_with_time(input_file, output_file, threshold, original_file, classed_file)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
