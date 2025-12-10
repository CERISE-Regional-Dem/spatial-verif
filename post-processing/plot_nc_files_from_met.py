#!/usr/bin/env python3
"""
Script to plot OBS vs FCST snow data from NetCDF files
Plots binary snow classification data for different regions and neighborhood smoothing values
"""

import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path
import argparse

def plot_snow_comparison(nc_file, output_dir=None, figsize=(16, 12)):
    """
    Plot OBS vs FCST snow data side by side for different regions and neighborhood values
    
    Parameters:
    -----------
    nc_file : str or Path
        Path to the NetCDF file
    output_dir : str or Path, optional
        Directory to save plots (if None, displays plots)
    figsize : tuple
        Figure size for each subplot grid
    """
    
    # Load the dataset
    ds = xr.open_dataset(nc_file)
    
    # Define the regions and neighborhood values to plot
    regions = ['FULL', 'NORTH_SCAND']
    nbrhd_values = [1, 25]
    
    # Get the date from the filename or dataset for titles
    try:
        init_time = ds.attrs.get('init_time', 'Unknown')
        if hasattr(ds, 'init_time'):
            init_time = str(ds.init_time.values)
        elif 'init_time' in ds.dims:
            init_time = str(ds.init_time.values[0]) if len(ds.init_time) > 0 else 'Unknown'
    except:
        init_time = Path(nc_file).stem.split('_')[-2] if '_' in Path(nc_file).stem else 'Unknown'
    
    # Set up the projection for Nordic region
    proj = ccrs.PlateCarree()
    
    for region in regions:
        for nbrhd in nbrhd_values:
            # Construct variable names
            if nbrhd == 1:
                obs_var = f'OBS_bin_snow_all_all_{region}_ge1'
                fcst_var = f'FCST_bin_snow_all_all_{region}_ge1'
            else:
                obs_var = f'OBS_bin_snow_all_all_{region}_ge1_NBRHD_{nbrhd}'
                fcst_var = f'FCST_bin_snow_all_all_{region}_ge1_NBRHD_{nbrhd}'
            
            # Check if variables exist in dataset
            if obs_var not in ds.variables or fcst_var not in ds.variables:
                print(f"Warning: Variables {obs_var} or {fcst_var} not found in dataset")
                continue
            
            # Create figure with subplots
            fig = plt.figure(figsize=figsize)
            
            # Plot OBS data
            ax1 = plt.subplot(131, projection=proj)
            obs_data = ds[obs_var]
            
            # Handle potential fill values
            fill_value = obs_data.attrs.get('_FillValue', -9999.0)
            obs_plot_data = obs_data.where(obs_data != fill_value, np.nan)
            
            im1 = ax1.pcolormesh(ds.lon, ds.lat, obs_plot_data, 
                               transform=proj, cmap='Blues', vmin=0, vmax=1)
            ax1.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax1.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax1.add_feature(cfeature.LAND, alpha=0.3, color='lightgray')
            ax1.set_title(f'OBS Snow\n{region} NBRHD_{nbrhd}', fontsize=12)
            ax1.gridlines(draw_labels=True, alpha=0.3)
            
            # Plot FCST data
            ax2 = plt.subplot(132, projection=proj)
            fcst_data = ds[fcst_var]
            
            # Handle potential fill values
            fill_value = fcst_data.attrs.get('_FillValue', -9999.0)
            fcst_plot_data = fcst_data.where(fcst_data != fill_value, np.nan)
            
            im2 = ax2.pcolormesh(ds.lon, ds.lat, fcst_plot_data,
                               transform=proj, cmap='Blues', vmin=0, vmax=1)
            ax2.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax2.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax2.add_feature(cfeature.LAND, alpha=0.3, color='lightgray')
            ax2.set_title(f'FCST Snow\n{region} NBRHD_{nbrhd}', fontsize=12)
            ax2.gridlines(draw_labels=True, alpha=0.3)
            
            # Plot difference (FCST - OBS)
            ax3 = plt.subplot(133, projection=proj)
            diff_data = fcst_plot_data - obs_plot_data
            
            im3 = ax3.pcolormesh(ds.lon, ds.lat, diff_data,
                               transform=proj, cmap='RdBu_r', vmin=-1, vmax=1)
            ax3.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax3.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax3.add_feature(cfeature.LAND, alpha=0.3, color='lightgray')
            ax3.set_title(f'FCST - OBS\n{region} NBRHD_{nbrhd}', fontsize=12)
            ax3.gridlines(draw_labels=True, alpha=0.3)
            
            # Add colorbars
            cbar1 = plt.colorbar(im1, ax=ax1, orientation='horizontal', 
                               pad=0.1, shrink=0.8, label='Snow presence (0-1)')
            cbar2 = plt.colorbar(im2, ax=ax2, orientation='horizontal',
                               pad=0.1, shrink=0.8, label='Snow presence (0-1)')
            cbar3 = plt.colorbar(im3, ax=ax3, orientation='horizontal',
                               pad=0.1, shrink=0.8, label='Difference')
            
            # Set overall title
            fig.suptitle(f'Snow Analysis - {region} Region (NBRHD_{nbrhd})\n'
                        f'Init Time: {init_time}', fontsize=14, y=0.95)
            
            plt.tight_layout()
            
            # Save or display
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(exist_ok=True)
                filename = f'snow_comparison_{region}_NBRHD_{nbrhd}_{init_time}.png'
                # Clean filename
                filename = filename.replace(':', '-').replace(' ', '_')
                plt.savefig(output_path / filename, dpi=300, bbox_inches='tight')
                print(f"Saved: {output_path / filename}")
            else:
                plt.show()
            
            plt.close()
    
    ds.close()

def plot_summary_grid(nc_file, output_dir=None):
    """
    Create a summary grid showing all combinations in one figure
    """
    ds = xr.open_dataset(nc_file)
    
    regions = ['FULL', 'NORTH_SCAND']
    nbrhd_values = [1, 25]
    
    # Create a 2x4 grid (2 regions x 4 plots per region: OBS_1, FCST_1, OBS_25, FCST_25)
    fig = plt.figure(figsize=(20, 10))
    proj = ccrs.PlateCarree()
    
    plot_idx = 1
    
    for i, region in enumerate(regions):
        for j, nbrhd in enumerate(nbrhd_values):
            # OBS plot
            ax_obs = plt.subplot(2, 4, plot_idx, projection=proj)
            obs_var = f'OBS_bin_snow_all_all_{region}_ge1_NBRHD_{nbrhd}'
            
            if obs_var in ds.variables:
                obs_data = ds[obs_var]
                fill_value = obs_data.attrs.get('_FillValue', -9999.0)
                obs_data = obs_data.where(obs_data != fill_value, np.nan)
                im = ax_obs.pcolormesh(ds.lon, ds.lat, obs_data,
                                     transform=proj, cmap='Blues', vmin=0, vmax=1)
                ax_obs.add_feature(cfeature.COASTLINE, linewidth=0.5)
                ax_obs.add_feature(cfeature.BORDERS, linewidth=0.3)
                ax_obs.set_title(f'OBS {region}\nNBRHD_{nbrhd}', fontsize=10)
                if j == 0 and i == 1:  # Only add colorbar once
                    plt.colorbar(im, ax=ax_obs, orientation='horizontal', pad=0.05, shrink=0.7)
            
            plot_idx += 1
            
            # FCST plot
            ax_fcst = plt.subplot(2, 4, plot_idx, projection=proj)
            fcst_var = f'FCST_bin_snow_all_all_{region}_ge1_NBRHD_{nbrhd}'
            
            if fcst_var in ds.variables:
                fcst_data = ds[fcst_var]
                fill_value = fcst_data.attrs.get('_FillValue', -9999.0)
                fcst_data = fcst_data.where(fcst_data != fill_value, np.nan)
                im = ax_fcst.pcolormesh(ds.lon, ds.lat, fcst_data,
                                      transform=proj, cmap='Reds', vmin=0, vmax=1)
                ax_fcst.add_feature(cfeature.COASTLINE, linewidth=0.5)
                ax_fcst.add_feature(cfeature.BORDERS, linewidth=0.3)
                ax_fcst.set_title(f'FCST {region}\nNBRHD_{nbrhd}', fontsize=10)
                if j == 0 and i == 1:  # Only add colorbar once
                    plt.colorbar(im, ax=ax_fcst, orientation='horizontal', pad=0.05, shrink=0.7)
            
            plot_idx += 1
    
    try:
        init_time = ds.attrs.get('init_time', Path(nc_file).stem)
    except:
        init_time = Path(nc_file).stem
    
    plt.suptitle(f'Snow Analysis Summary - {init_time}', fontsize=16, y=0.95)
    plt.tight_layout()
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        filename = f'snow_summary_{init_time}.png'.replace(':', '-').replace(' ', '_')
        plt.savefig(output_path / filename, dpi=300, bbox_inches='tight')
        print(f"Saved summary: {output_path / filename}")
    else:
        plt.show()
    
    plt.close()
    ds.close()

def main():
    """Main function to run the plotting script"""
    parser = argparse.ArgumentParser(description='Plot OBS vs FCST snow data from NetCDF files')
    parser.add_argument('input_file', help='Path to input NetCDF file')
    parser.add_argument('--output-dir', '-o', help='Output directory for plots')
    parser.add_argument('--summary-only', action='store_true', 
                       help='Create only summary grid plot')
    parser.add_argument('--individual-only', action='store_true',
                       help='Create only individual comparison plots')
    
    args = parser.parse_args()
    
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        return
    
    print(f"Processing: {input_file}")
    
    if not args.individual_only:
        print("Creating summary grid plot...")
        plot_summary_grid(input_file, args.output_dir)
    
    if not args.summary_only:
        print("Creating individual comparison plots...")
        plot_snow_comparison(input_file, args.output_dir)
    
    print("Done!")

if __name__ == "__main__":
    main()
