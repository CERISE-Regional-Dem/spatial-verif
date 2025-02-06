#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=48:00:00

DOM=NO-AR-CE

module load cdo

cd /ec/res4/scratch/nhd/CERISE/cerise_snow_verif
source .venv/bin/activate
cd /ec/res4/scratch/nhd/CERISE/CARRA1

for DATE in $(seq -w 20160501 20160531); do
python conv_snow_to_binsnow.py carra1_snow_${DATE}_${DOM}_reg.grib2 bin_snow_carra1_${DATE}_${DOM}_reg.nc
done
