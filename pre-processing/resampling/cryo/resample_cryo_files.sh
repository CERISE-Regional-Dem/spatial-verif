#!/usr/bin/env bash
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

ml gdal
ml nco
ml python3

# First, let's see what subdatasets are available in the cryo file
#gdalinfo /scratch/fab0/Projects/cerise/carra_snow_data/cryo/snowcover_daily_20151001.nc

OUTDIR=/ec/res4/scratch/nhd/CERISE/CRYO_resampled
INDIR=/scratch/fab0/Projects/cerise/carra_snow_data/cryo

for YYYY in 2015 2016 2017 2018 2019; do

if [[ $YYYY -lt 2016 ]]; then
MONTHS="10"
else
MONTHS="$(seq -w 1 12)"
fi
for MM in ${MONTHS}; do
PERIOD=$YYYY${MM}
maxday_month
for D in $(seq -w 1 $MAXDAY); do
DATE=${PERIOD}$D

# reate a VRT file for prob_snow
gdal_translate -of VRT \
    -a_srs "+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs" \
    -gcp 0 0 -757289.6417661756 -3141627.325742849 \
    -gcp 610 0 2291863.371285755 -3141627.325742849 \
    -gcp 0 627 -757289.6417661756 -7497.917245209217 \
    -gcp 610 627 2291863.371285755 -7497.917245209217 \
    "NETCDF:${INDIR}/snowcover_daily_${DATE}.nc:prob_snow" \
    temp_prob_snow.vrt


# vrt for classed valze
gdal_translate -of VRT \
    -a_srs "+proj=laea +lat_0=90 +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs" \
    -gcp 0 0 -757289.6417661756 -3141627.325742849 \
    -gcp 610 0 2291863.371285755 -3141627.325742849 \
    -gcp 0 627 -757289.6417661756 -7497.917245209217 \
    -gcp 610 627 2291863.371285755 -7497.917245209217 \
    "NETCDF:${INDIR}/snowcover_daily_${DATE}.nc:classed_value" \
    temp_classed_value.vrt



# Then warp using the VRT
gdalwarp -t_srs "+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0" \
         -te 537154.737195782 -1047009.29431937 2537154.73719578 1452990.70568063 \
         -ts 800 1000 \
         -r bilinear \
         temp_prob_snow.vrt \
         prob_snow_regridded.nc


# Warp classed_value
gdalwarp -t_srs "+R=6371000 +lat_0=80 +lat_1=80 +lat_2=80 +lon_0=-34 +no_defs +proj=lcc +type=crs +units=m +x_0=0 +y_0=0" \
         -te 537154.737195782 -1047009.29431937 2537154.73719578 1452990.70568063 \
         -ts 800 1000 \
         -r bilinear \
         temp_classed_value.vrt \
         classed_value_regridded.nc

# use ncrename to rename variable
ncrename -v Band1,prob_snow prob_snow_regridded.nc
ncrename -v Band1,classed_value classed_value_regridded.nc
mv prob_snow_regridded.nc $OUTDIR/cryo_snow_regridded_${DATE}.nc
mv classed_value_regridded.nc $OUTDIR/classed_value_regridded_${DATE}.nc
#python3 add_binary_snow.py $OUTDIR/cryo_snow_regridded_${DATE}.nc $OUTDIR/bin_snow_cryo_${DATE}.nc
python3 add_binary_snow_time.py $OUTDIR/cryo_snow_regridded_${DATE}.nc $OUTDIR/bin_snow_cryo_${DATE}.nc 80 ${INDIR}/snowcover_daily_${DATE}.nc
done
done
done
