import numpy as np
import xarray as xr
from scipy.ndimage import uniform_filter
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys


# This script is a Python implementation of the agreement scale method described in:
# Dey, S. R. A., Roberts, N. M., Plant, R. S., & Migliorini, S. (2016).
# A new method for the characterization and verification of local spatial
# predictability for convective-scale ensembles.
# Quarterly Journal of the Royal Meteorological Society, 142(698), 1982-1996.
# DOI: 10.1002/qj.2792


def similarity_D(a, b):
    """
    Calculates the similarity score D between two fields 'a' and 'b'.

    This is based on Equation 1 from Dey et al. (2016).
    'a' and 'b' are expected to be neighborhood averages at a given scale.
    """
    # Handle the case where both values are zero, as per the paper
    zero_both = (a == 0) & (b == 0)
    
    # Compute numerator and denominator
    numerator = (a - b)**2
    denominator = (a**2 + b**2)
    
    # Compute D, avoiding division by zero
    D = np.full_like(a, np.nan, dtype=float)
    np.divide(numerator, denominator, out=D, where=denominator != 0)

    # Per Dey et al. (2016), D is 1 if a=b=0. In the paper's formulation,
    # this happens when the neighborhood average is zero for both fields.
    # For a non-negative field like precipitation, this implies no precipitation
    # in the neighborhood for either field.
    D[zero_both] = 1.0
    
    # If one field is zero and the other is not, D will be 1.
    # (a-b)^2 / (a^2+b^2) = (-b)^2 / b^2 = 1 if a=0, b>0.
    
    return D

def window_mean_nan(mat, size):
    """
    Calculates the window mean for a 2D array with NaNs.
    
    Args:
        mat (np.ndarray): The input 2D array.
        size (int): The size of the square window (e.g., 3 for a 3x3 window).
        
    Returns:
        np.ndarray: The array of windowed means.
    """
    # Create a mask for NaN values
    nan_mask = np.isnan(mat)
    
    # Create a copy of the matrix and replace NaNs with 0 for calculation
    mat_no_nan = np.where(nan_mask, 0, mat)
    
    # Create a count of non-NaN values in the window
    counts = uniform_filter(np.where(nan_mask, 0.0, 1.0), size=size, mode='mirror')
    
    # Calculate the sum within the window
    sums = uniform_filter(mat_no_nan, size=size, mode='mirror')
    
    # Calculate the mean, avoiding division by zero
    mean_val = np.full_like(mat, np.nan, dtype=float)
    np.divide(sums, counts, out=mean_val, where=counts > 0)
    
    return mean_val


def agreement_scale_map(f1, f2, alpha=0.5, S_lim=80):
    """
    Calculates the agreement scale map based on Dey et al. (2016).

    Args:
        f1 (np.ndarray): First 2D field (e.g., forecast).
        f2 (np.ndarray): Second 2D field (e.g., observation).
        alpha (float): Tunable parameter for the agreement criterion (0 to 1).
        S_lim (int): Maximum scale (in grid points) to check.

    Returns:
        np.ndarray: 2D map of agreement scales.
    """
    ny, nx = f1.shape
    
    # Initialize agreement scale matrix SA with the maximum scale
    SA = np.full((ny, nx), S_lim, dtype=np.int32)
    
    print(f"Calculating agreement scales for {ny} x {nx} grid...")
    
    # Create a mask for valid (non-NaN) data points in the original fields
    valid_mask = ~np.isnan(f1) & ~np.isnan(f2)
    
    # Loop over scales from S = 0 to S_lim
    for S in range(S_lim + 1):
        if S % 10 == 0:
            print(f"  Processing scale S = {S}/{S_lim}")
            
        # At scale S=0, the neighborhood is the point itself.
        if S == 0:
            f1_bar = f1
            f2_bar = f2
        else:
            # The size of the filter window is (2*S + 1)
            filter_size = 2 * S + 1
            f1_bar = window_mean_nan(f1, size=filter_size)
            f2_bar = window_mean_nan(f2, size=filter_size)

        # Calculate similarity measure D (Eq. 1)
        D = similarity_D(f1_bar, f2_bar)
        
        # Calculate agreement criterion threshold D_crit (Eq. 3)
        D_crit = alpha + (1 - alpha) * S / S_lim
        
        # Find points where agreement is achieved (Eq. 2)
        agreement_achieved = (D <= D_crit)
        
        # Update SA for points that achieve agreement for the first time.
        # We only update points that are currently at S_lim and have valid data.
        update_mask = agreement_achieved & (SA == S_lim) & valid_mask
        SA[update_mask] = S
        
        # Check for early termination if all valid points have found their scale
        if np.all(SA[valid_mask] != S_lim):
            print(f"  All valid points converged at scale S = {S}")
            break
            
    print("Agreement scale calculation completed!")
    
    # Convert SA to float and set to NaN where input was NaN
    SA = SA.astype(float)
    SA[~valid_mask] = np.nan
    return SA

def plot_agreement_scales(obs_field, fc_field, SA_fo, output_filename="agreement_scales_FO.png"):
    """
    Creates and saves a 4-panel plot for agreement scales analysis.
    """
    # Create a color scale that matches the one in Dey et al. (2016)
    paper_colors = [
        "#7B162B", "#C32F2F", "#E94B2A", "#F97B3B",
        "#FDBF5B", "#FEE89A", "#FEF6C7", "#FFFFE5"
    ]
    dey_cmap = mcolors.ListedColormap(paper_colors[::-1])
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle('Agreement Scales Analysis (Dey et al. 2016)', fontsize=16)
    
    # Plot 1: Observations
    ax = axes[0, 0]
    im1 = ax.imshow(obs_field, cmap='viridis', origin='lower', vmin=0)
    ax.set_title("Observations")
    ax.set_xlabel("Grid X")
    ax.set_ylabel("Grid Y")
    plt.colorbar(im1, ax=ax, fraction=0.046, pad=0.04, label="Value")
    
    # Plot 2: Forecast
    ax = axes[0, 1]
    im2 = ax.imshow(fc_field, cmap='viridis', origin='lower', vmin=0)
    ax.set_title("Forecast")
    ax.set_xlabel("Grid X")
    ax.set_ylabel("Grid Y")
    plt.colorbar(im2, ax=ax, fraction=0.046, pad=0.04, label="Value")
    
    # Plot 3: Agreement Scales
    ax = axes[1, 0]
    im3 = ax.imshow(SA_fo, cmap=dey_cmap, origin='lower', vmin=0, vmax=np.nanmax(SA_fo))
    ax.set_title("Agreement Scales SA(fo)")
    ax.set_xlabel("Grid X")
    ax.set_ylabel("Grid Y")
    cbar = plt.colorbar(im3, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Agreement Scale (grid points)")
    
    # Plot 4: Histogram
    ax = axes[1, 1]
    valid_sa = SA_fo[~np.isnan(SA_fo)]
    if valid_sa.size > 0:
        ax.hist(valid_sa.flatten(), bins=50, color='lightblue', edgecolor='black')
        mean_val = np.nanmean(SA_fo)
        ax.axvline(mean_val, color='red', linestyle='dashed', linewidth=2)
        ax.legend([f'Mean: {mean_val:.2f}'])
    ax.set_title("Agreement Scales Distribution")
    ax.set_xlabel("Agreement Scale (grid points)")
    ax.set_ylabel("Frequency")
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(output_filename, dpi=150)
    print(f"\nVisualization saved as '{output_filename}'")

if __name__ == "__main__":
    # --- Parameters from Dey et al. (2016) ---
    alpha = 0.5
    S_lim = 80  # Maximum neighborhood half-width (grid points)
    
    # --- Data Loading and Preparation ---
    print("--- Loading data ---")
    
    # !!! USER ACTION REQUIRED !!!
    # Replace these placeholders with the actual paths to your data files
    # and the correct variable names within those files.
    
    obs_file_path = sys.argv[1]
    fc_file_path = sys.argv[2]
    png_path = sys.argv[3]
    #obs_file_path = "whole_area/snowcover_simple_20180202.nc"
    #fc_file_path = "whole_area/carra1_cryo_20180202.nc"

    obs_variable_name = "bin_snow"
    fc_variable_name = "bin_snow"

    try:
        # Load observation data using xarray
        # Use engine="h5netcdf" or "netcdf4" if needed
        obs_da = xr.open_dataset(obs_file_path)[obs_variable_name]
        
        # Load forecast data using xarray
        # Use engine="cfgrib" for GRIB files
        #fc_da = xr.open_dataset(fc_file_path, engine="cfgrib")[fc_variable_name]
        fc_da = xr.open_dataset(fc_file_path)[fc_variable_name]

        # --- Grid Alignment Check ---
        # The two fields MUST be on the same grid.
        # If they are not, you need to regrid one to match the other.
        # A library like 'xesmf' is recommended for this.
        # Example:
        # import xesmf as xe
        # regridder = xe.Regridder(fc_da, obs_da, 'bilinear')
        # fc_da_regridded = regridder(fc_da)
        # fc_field = fc_da_regridded.values
        
        # For this example, we assume grids are already aligned.
        obs_field = obs_da.values
        fc_field = fc_da.values
        
        # Ensure fields are 2D. If they have time or level dimensions, select one.
        if obs_field.ndim > 2:
            # Example: select the first time step
            obs_field = obs_field[0, :, :]
        if fc_field.ndim > 2:
            fc_field = fc_field[0, :, :]

        print("--- Data loaded successfully ---")

        # --- Main Execution ---
        print("\n=== CALCULATING AGREEMENT SCALES (Dey et al. 2016) ===\n")
        
        SA_fo = agreement_scale_map(fc_field, obs_field, alpha=alpha, S_lim=S_lim)
        
        # --- Results Summary ---
        print("\n=== RESULTS SUMMARY ===")
        if np.all(np.isnan(SA_fo)):
            print("Could not calculate agreement scales. Check input data.")
        else:
            print(f"Domain-mean agreement scale: {np.nanmean(SA_fo):.1f} grid points")
            print(f"Minimum agreement scale: {np.nanmin(SA_fo):.1f} grid points")
            print(f"Maximum agreement scale: {np.nanmax(SA_fo):.1f} grid points")
            print(f"Standard deviation: {np.nanstd(SA_fo):.1f} grid points")
        
        # --- Visualization ---
        plot_agreement_scales(obs_field, fc_field, SA_fo,png_path)

    except (FileNotFoundError, KeyError, AttributeError) as e:
        print("\n--- ERROR ---")
        print("Could not load or process data. Please check your file paths and variable names.")
        print(f"Details: {e}")
        print("\nThis script requires real data to run. Please update the placeholder paths.")

    print("\n=== AGREEMENT SCALES ANALYSIS COMPLETE ===")
