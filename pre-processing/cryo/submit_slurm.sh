#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate
OUTDIR=/ec/res4/scratch/nhd/CERISE/amsr2_test
cd /lus/h2resw01/scratch/nhd/CERISE/spatial-verif/pre-processing/cryo
INI="2016-01-01"
END="2016-12-31"
#CRYO




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

python dump_cerise_in_cryo_grid.py $INI $END
python dump_carra1_in_cryo_grid.py $INI $END

for YYYY in 2016 2017 2018 2019; do
if [[ $YYYY -lt 2016 ]]; then
MONTHS="10 11 12"
else
MONTHS="$(seq -w 1 12)"
fi
for MM in ${MONTHS}; do
PERIOD=$YYYY${MM}

maxday_month

for D in $(seq -w 1 $MAXDAY); do

  DATE=${PERIOD}$D
  python reformat_cryo.py /scratch/fab0/Projects/cerise/carra_snow_data/cryo/snowcover_daily_${DATE}.nc snowcover_simple_${DATE}.nc

done

done
done
