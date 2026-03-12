import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
import os

# Load the NetCDF file
ifile = "../../MET_CERISE_vs_CRYO_paper/grid_stat_000000L_20151122_120000V_pairs.nc"
ifile = sys.argv[1]
ds = xr.open_dataset(ifile)
file_name = os.path.basename(ifile)
time_str = file_name.split("_")[3]

# Extract the data
#prob_snow = ds['prob_snow'].squeeze()  # Remove time dimension if single timestep
obs = ds["OBS_bin_snow_0_all_all_FULL"].squeeze()
fcst = ds['FCST_bin_snow_0_all_all_FULL'].squeeze()
lat = ds['lat']
lon = ds['lon']

def simple_plots():
    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: fcst
    im1 = ax1.imshow(obs, cmap='Blues', vmin=0, vmax=1, origin='upper')
    ax1.set_title('Snow obs', fontsize=14, fontweight='bold')
    ax1.set_xlabel('X coordinate')
    ax1.set_ylabel('Y coordinate')
    cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
    cbar1.set_label('Binary Snow', rotation=270, labelpad=20)
    
    # Plot 2: Classified Values
    # Create a custom colormap for classified values
    # Assuming typical snow classification: 0=no snow, 1=snow, possibly other classes
    # Convert to numpy array and handle missing values properly
    fcst_array = fcst.values
    # For byte/integer data, check for fill values or specific missing value indicators
    #unique_vals = np.unique(classed_array)
    #print(f"Unique classified values: {unique_vals}")
    
    # Use a categorical colormap
    im2 = ax2.imshow(fcst.values, cmap='viridis', origin='upper')
    ax2.set_title('Snow Classification', fontsize=14, fontweight='bold')
    ax2.set_xlabel('X coordinate')
    ax2.set_ylabel('Y coordinate')
    cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
    cbar2.set_label('Classification Value', rotation=270, labelpad=20)
    
    # Add grid and improve appearance
    for ax in [ax1, ax2]:
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.suptitle('Snow Cover Data - October 1, 2015', fontsize=16, fontweight='bold', y=1.02)
    
    # Show statistics
    #print(f"Probability of Snow - Min: {np.nanmin(prob_snow):.3f}, Max: {np.nanmax(prob_snow):.3f}, Mean: {np.nanmean(prob_snow):.3f}")
    #print(f"Classified Values - Min: {np.min(classed_array):.0f}, Max: {np.max(classed_array):.0f}")
    #print(f"Data shape: {prob_snow.shape}")
    
    plt.show()

# Optional: Create a version with geographic projection if you want to use lat/lon
def create_geographic_plot():
    """
    Alternative version using geographic coordinates
    """
    fig = plt.figure(figsize=(16, 8))
    
    # Define the projection from the NetCDF metadata
    # Lambert Azimuthal Equal Area projection centered on North Pole
    proj = ccrs.LambertAzimuthalEqualArea(central_latitude=90, central_longitude=0)
    
    # Create subplots with cartopy projection
    ax1 = plt.subplot(1, 2, 1, projection=proj)
    ax2 = plt.subplot(1, 2, 2, projection=proj)
    
    # Plot 1: Probability of Snow
    #im1 = ax1.pcolormesh(lon, lat, obs, cmap='Blues', vmin=0, vmax=1, 
    #                    transform=ccrs.PlateCarree())
    im1 = ax1.pcolormesh(lon, lat, obs, cmap='viridis', vmin=0, vmax=1, 
                        transform=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE)
    ax1.add_feature(cfeature.BORDERS)
    ax1.set_title(f'Snow obs on {time_str}', fontsize=14, fontweight='bold')
    cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
    cbar1.set_label('Binary Snow', rotation=270, labelpad=20)
    
    # Plot 2: Classified Values
    im2 = ax2.pcolormesh(lon, lat, fcst, cmap='viridis', vmin=0,vmax=1,
                        transform=ccrs.PlateCarree())
    ax2.add_feature(cfeature.COASTLINE)
    ax2.add_feature(cfeature.BORDERS)
    ax2.set_title(f'Snow fcst on {time_str}', fontsize=14, fontweight='bold')
    cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
    cbar2.set_label('Binary snow', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.suptitle('Snow Cover Data - October 1, 2015 (Geographic)', fontsize=16, fontweight='bold', y=1.02)
    plt.show()

# Uncomment the line below to also create the geographic version
#simple_plots()
create_geographic_plot()

# Close the dataset
ds.close()
