#!/usr/bin/env bash
source env.sh

module load python3
INI=20160902
END=20160930

for DATE in $(seq -w $INI $END); do
#./run_resampling.sh $IMS_RAW/ims_${DATE}_1km_v1.3.nc

time_file=$IMS_RAW/ims_${DATE}_1km_v1.3.nc
snow_file=$IMS_RAW/ims_${DATE}_latlon_NO-AR-CE.nc
output_file=$IMS_RAW/bin_snow_ims_${DATE}_latlon_NO-AR-CE.nc
if [ -f $time_file ]; then
 python3 add_time.py $time_file $snow_file $output_file
else
 echo "Input file to generate binary snow not found: $time_file" 
fi

done

