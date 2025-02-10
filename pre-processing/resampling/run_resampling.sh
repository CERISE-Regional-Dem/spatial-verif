#!/usr/bin/env bash
# Resamples the IMS data to the CARRA1 grid
# IMS is 1km resolution, CARRA1 is 2km

source env.sh

atos_hosts=(ac6)

#if [[ ${atos_hosts[@]} =~ $HOSTNAME ]]; then
  echo "Assuming I am using atos. Loading cdo,nco,gdal"
  module load cdo
  module load nco
  module load gdal
#fi


#The file below gets the grid data
#it only needs the grid, not the variable. Any time step will do
DOM=NO-AR-CE
carra_grid=$CARRA1_RAW/228141_20150501_${DOM}_reg.grib2
if [ ! $carra_grid ]; then
echo "grib file $carra_grid with grid source not found!"
exit 1
fi

#
#dump grid from grib file. Do this only once for each domain
# This is only for comparison at the end or using the grid description instead of the source file
#cdo griddes $carra_grid > grib_desc.txt

if [ -z $1 ]; then
echo "Provide input file"
exit 1
else
input_file=$1
fi

cd $IMS_INT
#extract the variables
# This version with gdal works, but gives some errors
#gdal_translate -of netCDF -b 1 $input_file extracted_variables.nc
#
[ -f extracted_variables.nc ] && rm extracted_variables.nc
ncks -v IMS_Surface_Values,time $input_file extracted_variables.nc


# regrid to regular grid 
# Get some parts of the name. Not this assumes original
BDIR=$(dirname $input_file)
BFILE=$(basename $input_file)
readarray -d _ -t SPLIT <<< $BFILE #"$input_file" #split a string based on the delimiter '_'
reproj_file=$BDIR/${SPLIT[0]}_${SPLIT[1]}_latlon.nc
gdalwarp -t_srs EPSG:4326 -r near -of netCDF extracted_variables.nc $reproj_file #  ims2015121_1km_latlon.nc
#

#do the regridding
#cdo remapbil,$grib_source reprojected_output.nc regridded_output_CE.nc
regrid_file=$BDIR/${SPLIT[0]}_${SPLIT[1]}_latlon_${DOM}.nc
cdo remapbil,${carra_grid} ${reproj_file} $regrid_file 
#alternatively, use the grid description above: cdo remapbil,grid_desc.txt ${reproj_file} $regrid_file

## check the grid (optional)
#cdo griddes ${reproj_file}_${SPLIT}_latlon_${DOM}.nc
#echo "Original grid"
#cat grib_grid_carra1_west.txt 
