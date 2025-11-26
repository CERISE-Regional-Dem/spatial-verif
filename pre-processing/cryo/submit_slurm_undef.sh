#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

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


#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate
OUTDIR=/ec/res4/scratch/nhd/CERISE/amsr2_test
cd /lus/h2resw01/scratch/nhd/CERISE/spatial-verif/pre-processing/cryo
INI="2016-01-01"
END="2016-12-31"

for DATE in 20160503 20170529  20170608 20180509 20180204 20180218 20160222 20190206 20190204 20190203 20180219 20160125 20160122 20180122 20190202 20180202 20180130 20160107 20190130 20190201 20180129 20160108 20190129 20180203; do
#python dump_carra1_undefined.py $DATE $DATE
python dump_cerise_undefined.py $DATE $DATE
#python reformat_cryo_undefined.py /scratch/fab0/Projects/cerise/carra_snow_data/cryo/snowcover_daily_${DATE}.nc snowcover_undef_${DATE}.nc
done
