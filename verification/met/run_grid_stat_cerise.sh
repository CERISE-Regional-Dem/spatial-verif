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

MODEL=eraland
#only CERISE in this path
#FCPATH=/ec/res4/scratch/nhd/CERISE/${MODEL^^}_output #/from_zarr
FCPATH=/ec/res4/scratch/nhd/CERISE/ERA5/from_zarr
OBPATH=/ec/res4/scratch/nhd/CERISE/IMS_snow_cover/from_zarr
OUTPUT_DIR=/ec/res4/scratch/nhd/CERISE/MET_${MODEL^^}_vs_IMS_winter_2015

#CONFIG=config-files/GridStatConfig_ims_vs_${MODEL}
CONFIG=config-files/GridStatConfig_ims_vs_eraland

[ ! -d $OUTPUT_DIR ] && mkdir -p $OUTPUT_DIR

# $GP $FC fcst.ps 'name="FSNOWC"; level="Z0";'
for YYYY in 2015 2016; do

if [[ $YYYY -lt 2016 ]]; then
MONTHS="11 12"
else
MONTHS="$(seq -w 01 05)"
fi
for MM in ${MONTHS}; do
PERIOD=$YYYY${MM}
maxday_month
for D in $(seq -w 1 $MAXDAY); do
DATE=${PERIOD}$D
OB=$OBPATH/ims_${DATE}.nc
FC=$FCPATH/${MODEL}_${DATE}.nc
echo $OB
echo $FC
if [[ -f $OB ]] && [[ -f $FC ]]; then
$GS $FC $OB $CONFIG -outdir $OUTPUT_DIR -v 6
fi
done #D
done #MM
done #YYYY
