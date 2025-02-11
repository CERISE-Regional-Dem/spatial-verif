#!/usr/bin/env bash
#SBATCH --error=log_met.%j.err
#SBATCH --output=log_met.%j.out
#SBATCH --job-name=MET_verif
#SBATCH --qos=nf
#SBATCH --mem-per-cpu=64000


GS=/perm/nhd/MET/bin/grid_stat
GP=/perm/nhd/MET/bin/plot_data_plane

FCPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data/
OBPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data/

FCPATH=/ec/res4/scratch/nhd/CERISE/CERISE_output
FCPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data
#OBPATH=/perm/nhd/R/work_with_polly/harp_R433/ACCORD_VS_202406/sample_data/snow_data/IMS_regular_grid/
#OBPATH=/ec/res4/scratch/nhd/verification/R/IMS_regular_projected
OBPATH=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover
OBPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data
OUTPUT_DIR=/ec/res4/scratch/nhd/CERISE/MET_CERISE_vs_IMS
CONFIG=GridStatConfig_ims_vs_cerise

[ ! -d $OUTPUT_DIR ] && mkdir -p $OUTPUT_DIR
export MET_GRIB_TABLES=/perm/nhd/MET/share/met/table_files/grib2_for_cerise.txt

# $GP $FC fcst.ps 'name="FSNOWC"; level="Z0";'
for D in $(seq -w 1 30); do
DATE=201609$D
#OB=$OBPATH/bin_snow_ims_${DATE}_latlon_NO-AR-CE.nc
OB=$OBPATH/ims_${DATE}_1km_v1.3.nc
OB=$OBPATH/ims_${DATE}.nc
FC=$FCPATH/cerise_${DATE}.nc
##FC=$FCPATH/cerise_${DATE}_latlon.nc
echo $OB
echo $FC
if [[ -f $OB ]] && [[ -f $FC ]]; then
#$GS $FC $OB ./GridStatConfig_cerise_asmund -outdir /ec/res4/scratch/nhd/CERISE/MET_cerise -v 6
$GS $FC $OB $CONFIG -outdir $OUTPUT_DIR -v 6
fi
done
