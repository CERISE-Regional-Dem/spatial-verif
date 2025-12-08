#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00


source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate

convert_fc()
{
OUTDIR=/ec/res4/scratch/nhd/CERISE/CARRA_Land_pv2
[ ! -d $OUTDIR ] && mkdir $OUTDIR
MM=12
YYYY=2015
for DD in $(seq -w 1 31); do
#INPUT=/ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/$YYYY/$MM/$day/00/000/SURFOUT.${YYYY}${MM}${day}_03h00.nc 
INPUT=/ec/res4/scratch/fa7/Projects/CERISE/Data/scratch/nor3005/sfx_data/CARRA_Land_Pv2_stream_2015/archive/$YYYY/$MM/$DD/00/ensmean/SELECT_SURFOUT.${YYYY}${MM}${DD}_03h00.nc
echo $INPUT
OUT=$(basename $INPUT)
OUTPUT=$(basename $OUT .nc)_bin_snow.nc
if [ -f $INPUT ]; then
echo "Writing to $OUTPUT"
python convert_carra2_land2_to_bin_snow.py $INPUT $OUTDIR/$OUTPUT 
else
echo  "$INPUT not available! Stepping over this one"
fi
done
}

convert_ob()
{
OUTDIR=/ec/res4/scratch/nhd/CERISE/CRYO_orig_proj_CF_compliant
[ ! -d $OUTDIR ] && mkdir $OUTDIR
MM=12
YYYY=2015
for DD in $(seq -w 1 31); do
INPUT=/scratch/fab0/Projects/cerise/carra_snow_data/cryo/snowcover_daily_$YYYY$MM$DD.nc
echo $INPUT
OUT=$(basename $INPUT)
OUTPUT=$(basename $OUT .nc)_cf_compliant.nc
if [ -f $INPUT ]; then
echo "Writing to $OUTPUT"
python make_cryo_cf_compliant.py $INPUT $OUTDIR/$OUTPUT 
else
echo "$INPUT not available!"
fi
done
}

convert_fc
convert_ob
