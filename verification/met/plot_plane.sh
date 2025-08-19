#!/usr/bin/env bash
DP=/perm/nhd/MET/bin/plot_data_plane
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20160901.nc
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20180601.nc
FILE=/ec/res4/scratch/nhd/CERISE/amsr2_test/isba_binary_2018090100.nc
FILE=/ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/2018/09/01/00/000/SURFOUT.20180901_03h00.nc
FILE=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr/ims_20180901.nc
FILE=/ec/res4/scratch/nhd/CERISE/amsr2_test/isba_binary_2018093000.nc
FILE=SURFOUT.20180930_03h00_bin_snow_cf_compliant.nc

FILE=/ec/res4/scratch/nhd/CERISE/amsr2_test/SURFOUT.20180930_03h00_bin_snow.nc
OUT=test_mask.ps
OUT=ISBA_ims.ps
OUT=ISBA_20180901_version1.ps
OUT=ISBA_201809091_original_nc.ps
OUT=IMS_20180930.ps
OUT=ISBA_20180930.ps
#
FILE=/ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/zarr-data/ims_amsr2_20180930.nc
FILE=/ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/zarr-data/SURFOUT.20180930_03h00_bin_snow.nc
$DP $FILE $OUT 'name="bin_snow"; level="(0,*,*)"; file_type = NETCDF_NCCF;' -v 6
#$DP $FILE $OUT 'name="bin_snow"; level="(0,*,*)"; file_type = NETCDF_NCCF;' -v 6
#$DP $FILE $OUT 'name="DSN_T_ISBA"; level="(*,*)"; file_type = NETCDF_NCCF;' -v 6
#$DP $FILE $OUT 'name="bin_snow"; level="(*,*)"; file_type = NETCDF_NCCF;' -v 6
#$DP  masked_north.nc masked_north.ps 'name="NORTH"; level="(*,*)";' -v 6
#$DP $FILE $OUT 'name="binary_snow_cover"; level="(0,*,*)"; file_type = NETCDF_NCCF;' -v 6
