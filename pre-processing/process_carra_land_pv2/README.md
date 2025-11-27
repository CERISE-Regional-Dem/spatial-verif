# CARRA Land Pv2 Binary Snow Conversion

## Overview

This script converts CARRA Land Pv2 SURFEX model output files to CF-compliant NetCDF files containing binary snow cover data.

## Features

- Reads CARRA Land Pv2 SURFEX NetCDF files
- Creates binary snow cover variable based on snow depth threshold (default: 0.01 m)
- Generates CF-1.8 compliant NetCDF output
- Includes proper coordinate reference system (CRS) information
- Adds comprehensive metadata following CF and ACDD conventions

## Projection Support

The script automatically detects and handles two projection types:

### Polar Stereographic (CARRA Land Pv2)
- Used when `lat0 = 90`
- Parameters: lat0=90, lon0=-30, latc=84, lonc=-45
- Grid: 2869 x 2869, dx=2500m
- CF grid_mapping_name: `polar_stereographic`

### Lambert Conformal Conic
- Used when `lat0 < 90`
- CF grid_mapping_name: `lambert_conformal_conic`

## Usage

### Basic Usage

```bash
python convert_carra2_land2_to_bin_snow.py <input_file> <output_file>
```

### Example

```bash
python convert_carra2_land2_to_bin_snow.py \
    /path/to/SELECT_SURFOUT.20151015_03h00.nc \
    /path/to/output/SELECT_SURFOUT.20151015_03h00_bin_snow.nc
```

### Batch Processing with SLURM

See `submit_slurm.sh` for an example of batch processing multiple files.

## Input File Requirements

The input NetCDF file must contain:
- `DSN_T_ISBA`: Snow depth variable (in meters)
- `DX`: Grid spacing
- `xx`, `yy`: Grid dimensions

## Output File Structure

The output NetCDF file contains:

### Dimensions
- `time`: Time dimension (unlimited)
- `x`: X coordinate in projection space
- `y`: Y coordinate in projection space
- `nv`: Bounds dimension (2)

### Variables
- `bin_snow(time, y, x)`: Binary snow cover (0=no snow, 1=snow)
- `longitude(y, x)`: Longitude coordinates
- `latitude(y, x)`: Latitude coordinates
- `polar_stereographic` or `lambert_conformal_conic`: Grid mapping variable
- `time_bnds(time, nv)`: Time bounds
- `snow_depth_threshold`: Threshold value used for classification

### Coordinates
- `time`: Time coordinate with CF-compliant attributes
- `x`: Projection x-coordinate (meters)
- `y`: Projection y-coordinate (meters)

## CF Compliance

The output files follow CF-1.8 conventions:
- Proper grid mapping with all required attributes
- Standard coordinate variables with appropriate attributes
- Time encoding with bounds
- Comprehensive global attributes following ACDD recommendations
- Proper use of `grid_mapping` attribute linking data to projection

