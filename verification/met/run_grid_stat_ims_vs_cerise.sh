#!/usr/bin/env bash
#SBATCH --error=log_met.%j.err
#SBATCH --output=log_met.%j.out
#SBATCH --job-name=MET_verif
#SBATCH --qos=nf
#SBATCH --mem-per-cpu=64000

maxday_month()
{
    case ${MM} in
          01|03|05|07|08|10|12) MAXDAY="31";;
          04|06|09|11) MAXDAY="30";;
          02) MAXDAY="28";;
    esac
    check=`expr $YYYY % 4`
   #if [ $check -eq 0      ];
   if [ $check == 0  ];
        then
          if [ $MAXDAY -eq 28      ] ; then
            MAXDAY=29
          fi
    fi
}



GS=/perm/nhd/MET/bin/grid_stat
GP=/perm/nhd/MET/bin/plot_data_plane

FCPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data/
OBPATH=/ec/res4/scratch/nhd/CERISE/cerise_snow_verif/handling_zarr_data/

#OBPATH=/perm/nhd/R/work_with_polly/harp_R433/ACCORD_VS_202406/sample_data/snow_data/IMS_regular_grid/
#OBPATH=/ec/res4/scratch/nhd/verification/R/IMS_regular_projected
OBPATH=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr
FCPATH=/ec/res4/scratch/nhd/CERISE/CERISE_output
OUTPUT_DIR=/ec/res4/scratch/nhd/CERISE/MET_CERISE_vs_IMS_winter_2015
OUTPUT_DIR=/ec/res4/scratch/nhd/CERISE/MET_CERISE_vs_IMS_paper
CONFIG=config-files/GridStatConfig_ims_vs_cerise

[ ! -d $OUTPUT_DIR ] && mkdir -p $OUTPUT_DIR
export MET_GRIB_TABLES=/perm/nhd/MET/share/met/table_files/grib2_for_cerise.txt

for YYYY in 2015 2016 2017 2018 2019; do

if [[ $YYYY -lt 2016 ]]; then
MONTHS="09 10 11 12"
else
MONTHS="$(seq -w 1 12)"
fi
for MM in ${MONTHS}; do
PERIOD=$YYYY${MM}
maxday_month
for D in $(seq -w 1 $MAXDAY); do
DATE=${PERIOD}$D

# $GP $FC fcst.ps 'name="FSNOWC"; level="Z0";'
#for D in $(seq -w 1 15); do
#DATE=201511$D
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
done
done
