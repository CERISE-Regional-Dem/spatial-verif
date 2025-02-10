#!/bin/bash
source env.sh
# Fetch the IMS data. Note it will change the name
# of the file to one using the proper gregorian date

day_of_year() {
# Example usage:
# day_of_year "20160101" -> outputs 001
# day_of_year "20160510" -> outputs 131
    #date -d "$1" +%j
    DAY=$(date -d "$current_date" +%j)

}



cli()
{
current_date=$1
day_of_year 
YYYY=${1:0:4}
echo $YYYY $DAY
wget https://noaadata.apps.nsidc.org/NOAA/G02156/netcdf/1km/$YYYY/ims${YYYY}${DAY}_1km_v1.3.nc.gz .
}

all_dates()
{
cd $IMS_RAW
for current_date in $(seq -w $INI $END); do
day_of_year 
YYYY=${current_date:0:4}
echo $current_date $DAY
wget https://noaadata.apps.nsidc.org/NOAA/G02156/netcdf/1km/$YYYY/ims${YYYY}${DAY}_1km_v1.3.nc.gz .
if [ -f ims${YYYY}${DAY}_1km_v1.3.nc.gz ]; then
gunzip ims${YYYY}${DAY}_1km_v1.3.nc.gz
mv ims${YYYY}${DAY}_1km_v1.3.nc ims_${current_date}_1km_v1.3.nc
else
echo "WARNING: ims${YYYY}${DAY}_1km_v1.3.nc.gz not available!!!"
echo "Skipping..."
fi
done
cd -
}
INI=20160901
END=20160930
all_dates
