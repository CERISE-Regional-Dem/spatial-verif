# Zarr Data Pre-processing Scripts Documentation

This directory contains Python scripts for processing snow data in zarr data from the CARRA1_land_v1 (CERISE demonstrator) and putting them in the correct CF compliant format
that MET expects. All scripts handle data extraction, projection corrections, and CF-1.7 compliant NetCDF output generation.

## Overview

The scripts process snow cover data from multiple sources:
- **CARRA1**: CARRA reanalysis snow data
- **CERISE**: CERISE ensemble analysis data
- **ERA-Land**: ERA-Land reanalysis data
- **IMS**: Interactive Multisensor Snow and Ice Mapping System (observation)
- **ISBA**: SURFEX-ISBA land surface model outputs
- **AMSR2**: Advanced Microwave Scanning Radiometer 2 data

## Scripts

### 1. `dump_carra1.py`
**Purpose**: Extracts binary snow classification from CARRA1 reanalysis data

**Usage**:
```bash
python dump_carra1.py <date_ini> <date_end>
```

**Functionality**:
- Opens CARRA1 zarr dataset from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/carrasnow_v2.zarr`
- Extracts binary snow classification for specified date range
- Creates CF-1.7 compliant NetCDF with Lambert Conformal Conic projection
- Outputs binary snow presence (0/1) with proper grid mapping attributes

---

### 2. `dump_cerise.py`
**Purpose**: Processes CERISE ensemble analysis data to extract binary snow cover

**Usage**:
```bash
python dump_cerise.py <date_ini> <date_end>
```

**Functionality**:
- Opens CERISE analysis zarr dataset from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/ana_v2.zarr`
- Computes ensemble mean across members
- Creates binary snow classification based on snow height threshold (hxa > 0.01m)
- Outputs CF-1.7 compliant NetCDF with lat/lon coordinates
- Available data range: 2015-09 to 2019-08-05T06

---

### 3. `dump_eraland.py`
**Purpose**: Extracts binary snow classification from ERA-Land reanalysis

**Usage**:
```bash
python dump_eraland.py <date_ini> <date_end>
```

**Functionality**:
- Opens ERA-Land zarr dataset from `/ec/scratch/fab0/Projects/cerise/carra_snow_data/eraland.zarr/`
- Extracts binary snow data for specified date range
- Creates CF-1.7 compliant NetCDF with Lambert Conformal Conic projection
- Outputs standardized binary snow classification

---

### 4. `dump_ims.py`
**Purpose**: Processes IMS (Interactive Multisensor Snow and Ice Mapping System) data

**Usage**:
```bash
python dump_ims.py <date_ini> <date_end>
```

**Functionality**:
- Opens IMS zarr dataset from `/scratch/fab0/Projects/cerise/carra_snow_data/ims.zarr`
- Converts IMS surface values to binary snow classification (value 4 = snow present)
- Creates integer-based x/y coordinates
- Outputs CF-1.7 compliant NetCDF with Lambert Conformal Conic projection

---

### 5. `dump_isba.py`
**Purpose**: Converts SURFEX-ISBA SURFOUT files to CARRA-like NetCDF format

**Usage**:
```bash
python dump_isba.py <input_file> <output_path>
```

**Functionality**:
- Reads SURFOUT NetCDF files containing DSN_T_ISBA variable
- Extracts timestamp from file path/name
- Creates CARRA-like structure with:
  - Integer dimensions (y, x)
  - 1D coordinate variables
  - 2D auxiliary coordinate variables (x_2d, y_2d)
  - Scalar CRS variable with LCC attributes
- Outputs binary snow classification with proper metadata

---

### 6. `dump_isba_amsr2.py`
**Purpose**: Processes ISBA SURFOUT data and reprojects to AMSR2-compatible grid

**Usage**:
```bash
python dump_isba_amsr2.py <input_file> <output_path>
```

**Functionality**:
- Adapted from dump_cerise.py for ISBA data handling
- Implements `sfx2areadef()` function to convert SURFEX domain to pyresample AreaDefinition
- Supports both Lambert Conformal Conic (lcc) and Stereographic (stere) projections
- Reprojects ISBA data to match AMSR2 grid specifications
- Handles grid spacing (default 2500m) and projection parameters
- Outputs CF-1.7 compliant NetCDF

---

### 7. `ims_correct_projection.py`
**Purpose**: Corrects IMS data projection and creates proper CF-compliant coordinates

**Usage**:
```bash
python ims_correct_projection.py <date_ini> <date_end> <out_path>
```

**Functionality**:
- Opens IMS zarr dataset
- Creates proper projection coordinates using Lambert Conformal Conic parameters:
  - R=6371000, lat_0=80, lat_1=80, lat_2=80, lon_0=-34
  - Bounding box: [537154.737195782, -1047009.29431937, 2537154.73719578, 1452990.70568063]
  - Grid spacing: 2500m
- Converts IMS surface values to binary snow (value 4 = snow)
- Generates proper x/y coordinates in projection space (meters)
- Calculates lon/lat auxiliary coordinates
- Outputs CF-1.7 compliant NetCDF with corrected projection

---

### 8. `amsr2_correct_projection.py`
**Purpose**: Corrects AMSR2 data projection using IMS projection parameters

**Usage**:
```bash
python amsr2_correct_projection.py <input_file> <output_file> [--validate]
```

**Functionality**:
- Creates IMS-compatible projection coordinates
- Uses same Lambert Conformal Conic projection as IMS:
  - R=6371000, lat_0=80, lat_1=80, lat_2=80, lon_0=-34
  - Grid spacing: 2500m
- Implements `create_ims_projection_coords()` for coordinate generation
- Implements `calculate_ims_lonlat_coords()` for lon/lat calculation
- Reprojects AMSR2 data to match IMS grid
- Optional validation flag for quality checks
- Outputs CF-1.7 compliant NetCDF

---

### 9. `submit_slurm.sh`
**Purpose**: SLURM batch job submission script for running data processing pipelines

**Usage**:
```bash
sbatch submit_slurm.sh
```

**Configuration**:
- Memory: 64GB per CPU
- Time limit: 48 hours
- Python environment: `/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv`
- Output directory: `/ec/res4/scratch/nhd/CERISE/amsr2_test`

**Functionality**:
- Activates Python virtual environment
- Sets date range (2015-12-01 to 2019-08-01)
- Contains commented examples for running various dump scripts:
  - CERISE data extraction
  - CARRA1 data extraction
  - IMS data extraction
  - CRYO data extraction (currently active)
  - ISBA data processing with AMSR2 projection
- Includes loop for batch processing multiple days
- Demonstrates workflow for processing SURFOUT files

---

## Common Features

All scripts share these characteristics:

1. **CF-1.7 Compliance**: Output NetCDF files follow Climate and Forecast metadata conventions version 1.7
2. **Binary Snow Classification**: Convert various snow metrics to standardized binary format (0=no snow, 1=snow)
3. **Projection Handling**: Proper handling of Lambert Conformal Conic and other projections
4. **Grid Mapping**: Include CRS/grid_mapping variables with complete projection parameters
5. **Coordinate Systems**: Provide both projection coordinates (x, y in meters) and geographic coordinates (lon, lat)
6. **Metadata**: Include standard_name, long_name, units, and other CF attributes

## Projection Parameters

Most scripts use the IMS/CARRA Lambert Conformal Conic projection:
- **Projection**: Lambert Conformal Conic (lcc)
- **Latitude of origin**: 80.0°N
- **Standard parallels**: 80.0°N, 80.0°N
- **Central meridian**: -34.0°E
- **Sphere radius**: 6,371,000 m
- **Grid spacing**: 2,500 m
- **False easting/northing**: 0.0 m

## Dependencies

Required Python packages:
- xarray
- numpy
- pandas
- cartopy
- pyproj
- pyresample
- datetime
- uuid (for some scripts)

## Data Paths

Scripts reference data from:
- `/ec/scratch/fab0/Projects/cerise/carra_snow_data/` - CARRA, CERISE, ERA-Land, IMS zarr datasets
- `/ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/` - ISBA SURFOUT files (sample)
- `/ec/res4/scratch/nhd/CERISE/` - Output directories

## Notes

- Date formats: "YYYY-MM-DD" (e.g., "2016-09-01")
- Binary snow threshold: Typically 0.01m snow height or specific surface value codes
- All scripts handle time slicing for specified date ranges
- Output files are CF-1.7 compliant for interoperability with climate analysis tools
