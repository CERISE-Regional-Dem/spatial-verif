ml conda
conda activate glat
ml netcd4
cd MET-11.1.0/
#./configure --prefix=`pwd` --enable-grib2 --enable-python --enable-modis --enable-mode_graphics --enable-lidar2nc
make install
