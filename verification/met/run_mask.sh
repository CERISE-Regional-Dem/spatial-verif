#!/usr/bin/env bash
#SBATCH --error=log_mask.%j.err
#SBATCH --output=log_mask.%j.out
#SBATCH --job-name=mask_verif
#SBATCH --qos=nf
#SBATCH --mem-per-cpu=16000

#/perm/nhd/MET/bin/gen_vx_mask test.nc -type poly polygons/north_scandi_denser_inverted.poly out.nc

#FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20160901.nc
#/perm/nhd/MET/bin/gen_vx_mask $FILE -type poly polygons/north_inverted.poly masked_north.nc


FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20151101.nc
#/perm/nhd/MET/bin/gen_vx_mask $FILE -type poly polygons/north_sweden.poly north_sweden_mask.nc
/perm/nhd/MET/bin/gen_vx_mask $FILE -type poly polygons/north_part_only.poly north_part_mask.nc


FILE=/ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/cryo/snow_simple/snowcover_simple_20171107.nc
/perm/nhd/MET/bin/gen_vx_mask $FILE -type poly polygons/polygon_for_cryo_scand.poly poly_cryo_scand.nc
