#!/usr/bin/env bash
#SBATCH --error=log_met.%j.err
#SBATCH --output=log_met.%j.out
#SBATCH --job-name=MET_verif
#SBATCH --qos=nf
#SBATCH --mem-per-cpu=16000

MODE=/perm/nhd/MET/bin/mode 
OB=$SCRATCH/CERISE/IMS_snow_cover/from_zarr/ims_20151101.nc

FC=$SCRATCH/CERISE/CARRA1/from_zarr/carra1_20151101.nc
OUT=$SCRATCH/CERISE/MET_CARRA1_vs_IMS_winter_2015
$MODE $FC $OB $SCRATCH/CERISE/spatial-verif/verification/met/config-files/MODEConfig_snow -v 6 -outdir $OUT

FC=$SCRATCH/CERISE/CERISE_output/cerise_20151101.nc
OUT=$SCRATCH/CERISE/MET_CERISE_vs_IMS_winter_2015
$MODE $FC $OB $SCRATCH/CERISE/spatial-verif/verification/met/config-files/MODEConfig_snow -v 6 -outdir $OUT

OUT=$SCRATCH/CERISE/MET_ERALAND_vs_IMS_winter_2015
FC=$SCRATCH/CERISE/ERA5/from_zarr/eraland_20151101.nc
#$MODE fcst_file_list obs_file_list $SCRATCH/CERISE/spatial-verif/verification/met/config-files/MODEConfig_snow -v 6

