#!/usr/bin/env bash
DP=/perm/nhd/MET/bin/plot_data_plane
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20160901.nc
OUT=test_mask.ps
#
#$DP $FILE $OUT 'name="bin_snow"; level="(*,*)"; file_type = NETCDF_NCCF;' -v 6
$DP  masked_north.nc masked_north.ps 'name="NORTH"; level="(*,*)";' -v 6
