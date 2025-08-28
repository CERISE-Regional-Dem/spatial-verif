import numpy as np
import matplotlib.pyplot as plt
import xarray as xr
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Load the NetCDF file
ds = xr.open_dataset('snowcover_daily_20151001.nc')

# Extract the data
prob_snow = ds['prob_snow'].squeeze()  # Remove time dimension if single timestep
classed_value = ds['classed_value'].squeeze()
lat = ds['lat']
lon = ds['lon']

# Create figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Plot 1: Probability of Snow
im1 = ax1.imshow(prob_snow, cmap='Blues', vmin=0, vmax=100, origin='upper')
ax1.set_title('Snow Probability', fontsize=14, fontweight='bold')
ax1.set_xlabel('X coordinate')
ax1.set_ylabel('Y coordinate')
cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
cbar1.set_label('Probability of Snow', rotation=270, labelpad=20)

# Plot 2: Classified Values
# Create a custom colormap for classified values
# Assuming typical snow classification: 0=no snow, 1=snow, possibly other classes
# Convert to numpy array and handle missing values properly
classed_array = classed_value.values
# For byte/integer data, check for fill values or specific missing value indicators
unique_vals = np.unique(classed_array)
print(f"Unique classified values: {unique_vals}")

# Use a categorical colormap
im2 = ax2.imshow(classed_value, cmap='viridis', origin='upper')
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
print(f"Probability of Snow - Min: {np.nanmin(prob_snow):.3f}, Max: {np.nanmax(prob_snow):.3f}, Mean: {np.nanmean(prob_snow):.3f}")
print(f"Classified Values - Min: {np.min(classed_array):.0f}, Max: {np.max(classed_array):.0f}")
print(f"Data shape: {prob_snow.shape}")

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
    im1 = ax1.pcolormesh(lon, lat, prob_snow, cmap='Blues', vmin=0, vmax=100, 
                        transform=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE)
    ax1.add_feature(cfeature.BORDERS)
    ax1.set_title('Snow Probability', fontsize=14, fontweight='bold')
    cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
    cbar1.set_label('Probability of Snow', rotation=270, labelpad=20)
    
    # Plot 2: Classified Values
    im2 = ax2.pcolormesh(lon, lat, classed_value, cmap='viridis', 
                        transform=ccrs.PlateCarree())
    ax2.add_feature(cfeature.COASTLINE)
    ax2.add_feature(cfeature.BORDERS)
    ax2.set_title('Snow Classification', fontsize=14, fontweight='bold')
    cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
    cbar2.set_label('Classification Value', rotation=270, labelpad=20)
    
    plt.tight_layout()
    plt.suptitle('Snow Cover Data - October 1, 2015 (Geographic)', fontsize=16, fontweight='bold', y=1.02)
    plt.show()

# Uncomment the line below to also create the geographic version
# create_geographic_plot()

# Close the dataset
ds.close()
