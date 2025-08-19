#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=48:00:00


# Retrieves mars data for a whole month in a regular grid
OUTDIR=/ec/res4/scratch/nhd/CERISE/CARRA1
ORIGIN=NO-AR-CE
PERIOD=201605
INI=20160501
END=20160531
GRID="lambert" #original projection
GRID="reg" #regular lat lon (done via MARS)
TIME=0000
PARAM=141 #snow depth
PARAM=260038 #snow cover (%) NOT IN CARRA! Possibly in ERA5?
PARAM=228141 #snow depth water equivalent
PARAM=228141/33/260650/260289 #snow cover FRACTION (0 to 1)
OUTFILE=$OUTDIR/all_snow_${PERIOD}_${ORIGIN}_$GRID.grib2

for DATE in $(seq -w $INI $END); do
OUTFILE=$OUTDIR/carra1_snow_${DATE}_${ORIGIN}_$GRID.grib2
if [ $GRID == "reg" ] ; then
echo "Downloading in regular grid"
mars << eof
RETRIEVE,
    CLASS      = RR,
    TYPE       = AN,
    STREAM     = OPER,
    EXPVER     = prod,
    REPRES     = SH, 
    GRID       = 0.1/0.1,
    LEVTYPE    = SFC,
    PARAM      = $PARAM,
    DATE       = $DATE, #$INI/TO/$END,
    TIME       = 0000, #/0300/0600/0900/1200/1500/1800/2100,
    STEP       = 00,
    ORIGIN     = $ORIGIN,
    TARGET     = "$OUTFILE",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
else

echo "Downloading in lambert grid"
mars << eof
RETRIEVE,
    CLASS      = RR,
    TYPE       = AN,
    STREAM     = OPER,
    EXPVER     = prod,
    REPRES     = SH, 
    LEVTYPE    = SFC,
    PARAM      = $PARAM,
    DATE       = $DATE, #$INI/TO/$END,
    TIME       = $TIME,
    STEP       = 00,
    ORIGIN     = $ORIGIN,
    TARGET     = "$OUTFILE",
    PADDING    = 0,
    PROCESS    = LOCAL
eof
fi
done #date
