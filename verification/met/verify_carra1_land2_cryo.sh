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

ml apptainer
#apptainer shell /ec/res4/hpcperm/nhd/containers/met_12.1.0.sif
#GS=/perm/nhd/MET/bin/grid_stat
#GP=/perm/nhd/MET/bin/plot_data_plane

GS=grid_stat
GP=plot_data_plane


####OBPATH=/scratch/fab0/Projects/cerise/carra_snow_data/cryo
####FCPATH=/ec/res4/scratch/fa7/Projects/CERISE/Data/scratch/nor3005/sfx_data/CARRA_Land_Pv2_stream_2015/archive
OBPATH=/ec/res4/scratch/nhd/CERISE/CRYO_orig_proj_CF_compliant
FCPATH=/ec/res4/scratch/nhd/CERISE/CARRA_Land_pv2 ##/SELECT_SURFOUT.20151031_03h00_bin_snow.nc

OUTPUT_DIR=$SCRATCH/CERISE/MET_CARRA1_LAND2_CRYO

CONFIG=config-files-v12/GridStatConfig_for_CARRA2_CERISE_proj

[ ! -d $OUTPUT_DIR ] && mkdir -p $OUTPUT_DIR
export MET_GRIB_TABLES=/perm/nhd/MET/share/met/table_files/grib2_for_cerise.txt

for YYYY in 2015; do

if [[ $YYYY -lt 2016 ]]; then
MONTHS="10"
else
MONTHS="$(seq -w 1 12)"
fi
for MM in ${MONTHS}; do
PERIOD=$YYYY${MM}
maxday_month
for D in $(seq -w 15 $MAXDAY); do
DATE=${PERIOD}$D

#OB=$OBPATH/bin_snow_cryo_${DATE}.nc
#FC=$FCPATH/cerise_${DATE}.nc

OB=$OBPATH/snowcover_daily_${YYYY}${MM}${D}_cf_compliant.nc
FC=$FCPATH/SELECT_SURFOUT.${YYYY}${MM}${D}_03h00_bin_snow.nc
### FC=$FCPATH/$YYYY/$MM/$D/00/SELECT_SURFOUT.${YYYY}${MM}${D}_03h00.nc
echo $OB
echo $FC
if [[ -f $OB ]] && [[ -f $FC ]]; then
#$GS $FC $OB ./GridStatConfig_cerise_asmund -outdir /ec/res4/scratch/nhd/CERISE/MET_cerise -v 6
apptainer run /ec/res4/hpcperm/nhd/containers/met_12.1.0.sif $GS $FC $OB $CONFIG -outdir $OUTPUT_DIR -v 6
fi
done 
done
done
