#!/usr/bin/env bash
DP=/perm/nhd/MET/bin/plot_data_plane
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20160901.nc
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20180601.nc
FILE=/ec/res4/scratch/nhd/CERISE/amsr2_test/isba_binary_2018090100.nc
FILE=/ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/2018/09/01/00/000/SURFOUT.20180901_03h00.nc
FILE=/ec/res4/scratch/nhd/CERISE/amsr2_test/isba_binary_2018093000.nc
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20180901.nc
OUT=test_mask.ps
OUT=ISBA_ims.ps
OUT=ISBA_20180901_version1.ps
OUT=ISBA_201809091_original_nc.ps
OUT=ISBA_20180930.ps
OUT=IMS_20180930.ps
#
#$DP $FILE $OUT 'name="DSN_T_ISBA"; level="(*,*)"; file_type = NETCDF_NCCF;' -v 6
$DP $FILE $OUT 'name="bin_snow"; level="(*,*)"; file_type = NETCDF_NCCF;' -v 6
#$DP  masked_north.nc masked_north.ps 'name="NORTH"; level="(*,*)";' -v 6
