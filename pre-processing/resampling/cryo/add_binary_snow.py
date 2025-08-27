#!/usr/bin/env python3
"""
Script to add a binary snow variable to NetCDF files.
Creates bin_snow = 1 where prob_snow >= 0.8, else 0.
"""

import sys
import numpy as np
import netCDF4 as nc
from pathlib import Path

def add_binary_snow(input_file, output_file=None, threshold=0.8):
    """
    Add binary snow variable to NetCDF file.
    
    Parameters:
    -----------
    input_file : str
        Path to input NetCDF file
    output_file : str, optional
        Path to output NetCDF file. If None, creates based on input filename
    threshold : float, default 0.8
        Threshold for binary classification
    """
    
    if output_file is None:
        # Create output filename by adding '_with_bin' before the extension
        input_path = Path(input_file)
        output_file = input_path.parent / f"{input_path.stem}_with_bin{input_path.suffix}"
    
    print(f"Processing: {input_file}")
    print(f"Output: {output_file}")
    print(f"Threshold: {threshold}")
    
    # Read the input file
    with nc.Dataset(input_file, 'r') as src:
        # Check if prob_snow exists
        if 'prob_snow' not in src.variables:
            raise ValueError("Variable 'prob_snow' not found in input file")
        
        # Create output file
        with nc.Dataset(output_file, 'w') as dst:
            # Copy global attributes
            dst.setncatts(src.__dict__)
            
            # Copy dimensions
            for name, dimension in src.dimensions.items():
                dst.createDimension(
                    name, (len(dimension) if not dimension.isunlimited() else None)
                )
            
            # Copy all existing variables
            for name, variable in src.variables.items():
                # Create variable with same type and dimensions
                var = dst.createVariable(
                    name, variable.datatype, variable.dimensions,
                    fill_value=getattr(variable, '_FillValue', None)
                )
                
                # Copy variable attributes
                var.setncatts(variable.__dict__)
                
                # Copy data
                var[:] = variable[:]
            
            # Read prob_snow data
            prob_snow = src.variables['prob_snow'][:]
            
            # Create bin_snow variable
            bin_snow_var = dst.createVariable(
                'bin_snow', 'i1', ('y', 'x'),  # int8 type
                fill_value=-1  # Use -1 for missing data
            )
            
            # Set attributes for bin_snow
            bin_snow_var.long_name = "Binary snow cover flag"
            bin_snow_var.description = f"Binary flag: 1 where prob_snow >= {threshold}, 0 otherwise"
            bin_snow_var.units = "1"
            bin_snow_var.grid_mapping = "lambert_conformal_conic"
            bin_snow_var.valid_range = np.array([0, 1], dtype='i1')
            
            # Calculate binary snow
            # Handle NaN values in prob_snow
            bin_snow_data = np.full_like(prob_snow, -1, dtype='i1')  # Initialize with fill value
            
            # Set valid data points
            valid_mask = ~np.isnan(prob_snow)
            bin_snow_data[valid_mask] = (prob_snow[valid_mask] >= threshold).astype('i1')
            
            # Write the data
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
        print("Usage: python add_binary_snow.py input_file.nc [output_file.nc] [threshold]")
        print("\nExamples:")
        print("  python add_binary_snow.py cryo_snow_regridded_20150908.nc")
        print("  python add_binary_snow.py input.nc output.nc")
        print("  python add_binary_snow.py input.nc output.nc 75.0")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 80.
    
    try:
        add_binary_snow(input_file, output_file, threshold)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
