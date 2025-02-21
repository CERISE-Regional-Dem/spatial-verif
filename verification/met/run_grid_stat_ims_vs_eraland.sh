#!/usr/bin/env bash
#SBATCH --error=log_met.%j.err
#SBATCH --output=log_met.%j.out
#SBATCH --job-name=MET_verif
#SBATCH --qos=nf
#SBATCH --mem-per-cpu=64000


GS=/perm/nhd/MET/bin/grid_stat
GP=/perm/nhd/MET/bin/plot_data_plane

FCPATH=/ec/res4/scratch/nhd/CERISE/ERA5/from_zarr
OBPATH=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr
OUTPUT_DIR=/ec/res4/scratch/nhd/CERISE/MET_ERALAND_vs_IMS_winter_2015
CONFIG=config-files/GridStatConfig_ims_vs_eraland

[ ! -d $OUTPUT_DIR ] && mkdir -p $OUTPUT_DIR

# $GP $FC fcst.ps 'name="FSNOWC"; level="Z0";'
for D in $(seq -w 1 15); do
DATE=201511$D
OB=$OBPATH/ims_${DATE}.nc
FC=$FCPATH/eraland_${DATE}.nc
echo $OB
echo $FC
if [[ -f $OB ]] && [[ -f $FC ]]; then
$GS $FC $OB $CONFIG -outdir $OUTPUT_DIR -v 6
fi
done
