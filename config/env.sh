export IMS_RAW=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover
export IMS_INT=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/resampled
export CARRA1_RAW=/ec/res4/scratch/nhd/CERISE/CARRA1
export CARRA2_RAW=/ec/res4/scratch/nhd/CERISE/CARRA2
export CERISE_RAW=/ec/res4/scratch/nhd/CERISE/CERISE_output

[ ! -d $IMS_RAW ] && mkdir -p $IMS_RAW
[ ! -d $IMS_INT ] && mkdir -p $IMS_INT
