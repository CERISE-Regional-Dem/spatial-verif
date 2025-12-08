# MET Verification Workflow Guide

## Overview
This guide explains how to run the MET (Model Evaluation Tools) package `grid_stat` to compare  CARRA Land Pv1,2 against ISM or CRYO observations, including the data preprocessing steps required.


## Data Preprocessing

The input data must be in `netcdf` or `grib` format.

The main issue when using the original netcdf data from the CARRA Land1 or Land2 is that
the files are not CF compliant.
Additionally, the variables must include a binary variable `bin_snow`, set to 0 when there is snow
and to 1 when there is no snow (according to some threshold).


Some example conversion scripts are included below.

### Converting Data to CF-Compliant Format

Before running the verification, the original data must be converted to CF-compliant NetCDF format using:

**Script:** `pre-processing/process_carra_land_pv2/submit_slurm.sh`

#### Prerequisites
- Python conversion scripts:
  - `convert_carra2_land2_to_bin_snow.py` - Converts CARRA Land Pv2 forecast data
  - `make_cryo_cf_compliant.py` - Converts CRYO observation data to CF-compliant format

#### What the Preprocessing Does

The script contains two main functions:

**1. `convert_fc()` - Forecast Data Conversion**
- **Input:** CARRA Land Pv2 SURFOUT files from `/ec/res4/scratch/fa7/Projects/CERISE/Data/scratch/nor3005/sfx_data/CARRA_Land_Pv2_stream_2015/archive/$YYYY/$MM/$DD/00/ensmean/`
- **Output:** Binary snow files in `/ec/res4/scratch/nhd/CERISE/CARRA_Land_pv2/`
- **Format:** `SELECT_SURFOUT.YYYYMMDD_03h00_bin_snow.nc`
- **Process:** Extracts and converts snow variables to binary format suitable for MET verification

**2. `convert_ob()` - Observation Data Conversion**
- **Input:** Original CRYO snow cover data from `/scratch/fab0/Projects/cerise/carra_snow_data/cryo/`
- **Output:** CF-compliant files in `/ec/res4/scratch/nhd/CERISE/CRYO_orig_proj_CF_compliant/`
- **Format:** `snowcover_daily_YYYYMMDD_cf_compliant.nc`
- **Process:** Converts CRYO data to CF (Climate and Forecast) metadata conventions, ensuring compatibility with MET tools

#### Running the Preprocessing

```bash
# Submit as SLURM job
sbatch pre-processing/process_carra_land_pv2/submit_slurm.sh

# Or run interactively
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate
bash pre-processing/process_carra_land_pv2/submit_slurm.sh
```


## MET Verification

### Running the Verification Script
A sample verification script for CARRA1_LAND_PV2 can be found here:

**Script:** `verification/met/verify_carra1_land2_cryo.sh`

#### MET Installation via Apptainer

The script uses MET version 12.1.0 installed in an Apptainer container:

**Container Location:** `/ec/res4/hpcperm/nhd/containers/met_12.1.0.sif`

**Key Components:**
- `grid_stat` - MET tool for grid-to-grid verification statistics
- `plot_data_plane` - MET tool for plotting gridded data

#### Prerequisites

1. **Load Apptainer module:**
   ```bash
   ml apptainer
   ```

2. **Required Data Paths:**
   - **Observations:** `/ec/res4/scratch/nhd/CERISE/CRYO_orig_proj_CF_compliant/`
   - **Forecasts:** `/ec/res4/scratch/nhd/CERISE/CARRA_Land_pv2/`
   - **Output Directory:** `$SCRATCH/CERISE/MET_CARRA1_LAND2_CRYO`

3. **Configuration Files:**
   - **MET Config:** `config-files-v12/GridStatConfig_for_CARRA2_CERISE_proj`
   - **GRIB Tables:** `/perm/nhd/MET/share/met/table_files/grib2_for_cerise.txt`

#### How the Script Works

1. **Loads Apptainer module** to access container runtime
2. **Sets up paths** for observations, forecasts, and output
3. **Loops through dates** (currently configured for October 15-31, 2015)
4. **For each date:**
   - Checks if both observation and forecast files exist
   - Runs `grid_stat` inside the Apptainer container
   - Generates verification statistics

#### Running the Verification

**As SLURM Job:**
```bash
sbatch verification/met/verify_carra1_land2_cryo.sh
```

**SLURM Configuration:**
- Job name: MET_verif
- QOS: nf
- Memory: 64GB per CPU
- Logs: `log_met.<job_id>.err` and `log_met.<job_id>.out`

**Interactively:**
```bash
ml apptainer
export MET_GRIB_TABLES=/perm/nhd/MET/share/met/table_files/grib2_for_cerise.txt
export SCRATCH=/path/to/scratch  # Set your scratch directory

# Run for a specific date
YYYY=2015
MM=10
DD=15
OB=/ec/res4/scratch/nhd/CERISE/CRYO_orig_proj_CF_compliant/snowcover_daily_${YYYY}${MM}${DD}_cf_compliant.nc
FC=/ec/res4/scratch/nhd/CERISE/CARRA_Land_pv2/SELECT_SURFOUT.${YYYY}${MM}${DD}_03h00_bin_snow.nc
OUTPUT_DIR=$SCRATCH/CERISE/MET_CARRA1_LAND2_CRYO

apptainer run /ec/res4/hpcperm/nhd/containers/met_12.1.0.sif grid_stat \
  $FC $OB config-files-v12/GridStatConfig_for_CARRA2_CERISE_proj \
  -outdir $OUTPUT_DIR -v 6
```

#### Apptainer Command Breakdown

```bash
apptainer run /ec/res4/hpcperm/nhd/containers/met_12.1.0.sif grid_stat $FC $OB $CONFIG -outdir $OUTPUT_DIR -v 6
```

- `apptainer run` - Executes a command inside the container
- `/ec/res4/hpcperm/nhd/containers/met_12.1.0.sif` - MET container image
- `grid_stat` - MET verification tool
- `$FC` - Forecast file (CARRA Land Pv2)
- `$OB` - Observation file (CRYO)
- `$CONFIG` - GridStat configuration file
- `-outdir $OUTPUT_DIR` - Output directory for statistics
- `-v 6` - Verbosity level (6 = detailed output)

### Output

Verification statistics are written to: `$SCRATCH/CERISE/MET_CARRA1_LAND2_CRYO/`

Output includes:
- Grid statistics (accuracy, bias, correlation, etc.)
- Contingency tables
- NetCDF files with matched pairs
- ASCII stat files

## Workflow Summary

1. **Preprocess Data** → Convert original CARRA and CRYO data to CF-compliant format
2. **Load Apptainer** → Access MET tools via container
3. **Run Verification** → Execute grid_stat for each date pair
4. **Analyze Results** → Review statistics in output directory

## Customization

To modify the verification period, edit `verify_carra1_land2_cryo.sh`:

```bash
# Line 46-56: Change year, months, and days
for YYYY in 2015; do
  MONTHS="10"  # Change months
  for MM in ${MONTHS}; do
    for D in $(seq -w 15 $MAXDAY); do  # Change start day (15)
```
