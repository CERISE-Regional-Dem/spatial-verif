# Python scripts to plot data

## Overview
This is a brief summary of all python scripts used for plotting the data dump from MET. 
A bit disorganized but maybe useful.

## Detailed Script Descriptions

### 1. Data Visualization - Zarr Files 

#### `plot_ims_zarr.py` 
**Purpose:** Plots binary snow cover data from IMS (Interactive Multisensor Snow and Ice Mapping System) zarr files.
- Reads IMS zarr data from `/scratch/fab0/Projects/cerise/carra_snow_data/ims.zarr`
- Converts IMS surface values to binary snow classification (snow=1, no snow=0)
- Creates map visualizations with coastlines and borders using Cartopy
- Takes date as command-line argument
- Outputs PNG files named `ims_{date}.png`

#### `plot_carra1_zarr.py` 
**Purpose:** Plots binary snow cover data from CARRA1 East reanalysis zarr files.
- Reads CARRA1 zarr data from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/carrasnow_v2.zarr`
- Calculates binary snow using snow depth (sd) and snow density (rsn) ratio > 0.01
- Creates map visualizations with geographic features
- Takes date as command-line argument
- Outputs PNG files named `carra_{date}.png`

#### `plot_cerise_zarr.py` 
**Purpose:** Plots binary snow cover data from CERISE ensemble analysis zarr files.
- Reads CERISE zarr data from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/ana_v2.zarr`
- Computes ensemble mean across members
- Converts snow height analysis (hxa) to binary snow (threshold > 0.01)
- Creates map visualizations
- Takes date as command-line argument
- Outputs PNG files named `cerise_{date}.png`

#### `plot_eraland_zarr.py` 
**Purpose:** Plots binary snow cover data from ERA-Land reanalysis zarr files.
- Reads ERA-Land zarr data from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/eraland.zarr`
- Calculates binary snow using snow depth and density (note: uses 1000x multiplier for unit conversion)
- Creates map visualizations
- Takes date as command-line argument
- Outputs PNG files named `eraland_{date}.png`

---

### 2. FSS (Fractions Skill Score) Analysis - Basic 

#### `make_fss_plots.py` 
**Purpose:** Creates FSS heatmap visualizations for model verification against IMS data.
This script was used to produce the plots in the poster presentation
for the CERISE general meeting in March 2025.

- Reads MET (Model Evaluation Tools) output files (_cts.txt and _nbrcnt.txt)
- Processes FSS data for different neighborhood sizes
- Creates heatmaps showing FSS scores across dates and spatial scales
- Includes multiple regions (FULL, NORTH_SWEDEN, tested over CARRA1 east domain)
- Generates both standard and threshold-based (red/green) heatmaps
- Configurable for different models (ERALAND, CARRA1, CERISE) and time periods
- Outputs PNG files with naming pattern `fss_heatmap_{model}_{year}.png`


### 3. FSS Analysis - Extended Versions 

#### `make_fss_plots_all.py` 
**Purpose:** Extended version of FSS plotting for comprehensive analysis across all available data.
- Similar to `make_fss_plots.py` but processes all available time periods
- Batch processing 

#### `make_fss_plots_amsr2.py`
**Purpose:** Specialized FSS plotting for AMSR2 satellite data verification.
- Adapted for AMSR2 passive microwave snow cover data
- Processes verification statistics against AMSR2 observations
- Creates FSS heatmaps specific to AMSR2 comparisons

#### `make_fss_plots_publication.py` 
**Purpose:** Creates publication-quality FSS heatmap plots with enhanced styling.

- Publication-friendly formatting (serif fonts, specific DPI settings)
- Enhanced visual styling for scientific papers
- Configurable for specific time periods (e.g., November 2015)
- Uses seaborn whitegrid style with custom matplotlib parameters
- Outputs both PNG and PDF formats

#### `make_plots_fss_extended.py`
**Purpose:** Extended FSS plotting with additional analysis metrics and visualizations.
- More comprehensive FSS analysis beyond basic heatmaps (exploring other ways to visualize the data)
- Additional statistical plots and metrics

#### `make_plots_fss_extended_CARRA1_LAND2.py` 
**Purpose:** Specialized extended FSS plotting for CARRA1 Land version 2 data.
**Key Features:**
- Adapted for CARRA1 Land v2 specific data format
- Extended analysis tailored to this dataset

---

### 4. FSS Time Series Analysis

#### `time_series_fss.py` 
**Purpose:** Creates comprehensive time series visualizations of FSS scores.
- Processes FSS data over extended time periods (2015-2019)
- Creates time series plots showing FSS evolution
- Plots multiple regions (FULL, NORTH_SWEDEN)
- Configurable for different models (CERISE, CARRA1, ERALAND)

#### `selected_fss_time_series.py` 
**Purpose:** Creates time series plots for selected/specific time periods or regions.
- Focused analysis on user-selected periods
- Similar styling to `time_series_fss.py`
- Allows for targeted temporal analysis

---

### 5. FSS Comparison Scripts 

#### `compare_fss_time_series.py` 
**Purpose:** Compares FSS time series between different models (CERISE vs CARRA1).
- Side-by-side comparison of multiple models
- Publication-quality styling
- Color-coded model differentiation (blue for CERISE, orange for CARRA1)
- Loads and processes FSS data from multiple model directories
- Creates comparative visualizations (time series, boxplots, scatter plots)
- Plots multiple regions and neighborhood sizes

#### `compare_fss_highlight.py` 
**Purpose:** Creates FSS comparison plots with highlighted specific features or periods.
**Key Features:**
- Similar to `compare_fss_time_series.py` with emphasis highlighting
- Useful for drawing attention to specific events or periods

#### `compare_focus_winters_fss_time_series.py` 
**Purpose:** Focused comparison of FSS during winter seasons.
**Key Features:**
- Specialized for winter period analysis
- Compares model performance during snow-critical seasons
- Publication-quality formatting

#### `compare_fss_time_series_CARRA1_Land2.py` ✗ NOT IN REPOSITORY
**Purpose:** Specialized comparison including CARRA1 Land version 2 data.
**Key Features:**
- Three-way comparison (CERISE, CARRA1, CARRA1 Land v2)
- Adapted for CARRA1 Land v2 data format

---

### 6. Monthly FSS Analysis 

#### `monthly_fss_analysis.py` 
**Purpose:** Performs monthly aggregation and analysis of FSS scores.
- Monthly averaging of FSS scores
- Seasonal pattern analysis
- Publication-quality styling with colorblind-friendly palette
- Creates monthly comparison plots between models
- Plots multiple regions (FULL, NORTH_SCAND)
- Generates monthly heatmaps and time series
- Outputs organized by region in subdirectories

---

### 7. Interactive Polygon Selection Tools 

#### `select_a_polygon_MET_file.py` 
**Purpose:** Interactive polygon selection specifically for MET verification output files.
- Allows selection of verification regions on MET output
- Outputs coordinates in lat/lon format
- Useful for defining custom verification masks
When using this script one can define a polygon on the screen
using an nc file produced by MET and then use this
polygon to select a region in the verification (using grid_stat).

#### `plot_selected_polygon_MET_file.py` 
**Purpose:** Visualizes previously selected polygons on MET verification files.
- Loads and displays polygon selections
- Overlays polygons on verification data
- Useful for verifying region selections

---

### 8. NetCDF Visualization Tools 

#### `plot_nc_files_from_met.py` 
**Purpose:** Plotting for MET verification NetCDF output files.
- Plots OBS vs FCST snow data side-by-side
- Creates comparison plots with Cartopy projections
- Command-line interface with argparse
- Outputs organized plots for different configurations
- Includes coastlines, borders, and gridlines


#### `plot_variables_nc_files.py` 
**Purpose:** General-purpose NetCDF variable plotting tool.
**Key Features:**
- Plots various variables from NetCDF files
- Useful for exploratory data analysis


---
