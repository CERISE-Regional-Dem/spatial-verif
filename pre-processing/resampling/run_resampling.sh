#!/usr/bin/env bash
#it only needs the grid, not the variable. Any time step will do
DOM=NO-AR-CE
grib_source=../CARRA1/228141_20150501_${DOM}_reg.grib2

#
#dump grid from grib file. Do this only once for each domain
# This is only for comparison at the end
#cdo griddes $grib_source > grib_grid_carra1_west.txt

if [ -z $1 ]; then
echo "Provide input file"
exit 1
else
input_file=$1
fi

#extract the variables
# This version with gdal works, but gives some errors
#gdal_translate -of netCDF -b 1 $input_file extracted_variables.nc
#
[ -f extracted_variables.nc ] && rm extracted_variables.nc
ncks -v IMS_Surface_Values,time $input_file extracted_variables.nc


# regrid to regular grid 
# Get some parts of the name. Not this assumes original
readarray -d _ -t SPLIT <<<"$input_file" #split a string based on the delimiter '_'
reproj_file=${SPLIT[0]}_${SPLIT[1]}_latlon.nc
gdalwarp -t_srs EPSG:4326 -r near -of netCDF extracted_variables.nc $reproj_file #  ims2015121_1km_latlon.nc
#

#do the regridding
#cdo remapbil,$grib_source reprojected_output.nc regridded_output_CE.nc
regrid_file=${SPLIT[0]}_${SPLIT[1]}_latlon_${DOM}.nc
cdo remapbil,${grib_source} ${reproj_file} $regrid_file #   ${SPLIT}_latlon_${DOM}.nc

## check the grid (optional)
#cdo griddes ${reproj_file}_${SPLIT}_latlon_${DOM}.nc
#echo "Original grid"
#cat grib_grid_carra1_west.txt 
