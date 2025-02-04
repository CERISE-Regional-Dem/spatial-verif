for DATE in $(seq -w 20160501 20160531); do
time_file=ims_${DATE}_1km_v1.3.nc
snow_file=ims_${DATE}_latlon_NO-AR-CE.nc
output_file=bin_snow_ims_${DATE}_latlon_NO-AR-CE.nc
if [ -f $time_file ]; then
 python add_time.py $time_file $snow_file $output_file
fi
done

