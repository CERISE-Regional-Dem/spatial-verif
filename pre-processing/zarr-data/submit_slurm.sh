#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate

cd /ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/zarr-data
INI="2018-06-01"
END="2018-06-30"
#CERISE
#python dump_cerise.py $INI $END

#CARRA1
#python dump_carra1.py $INI $END
#IMS
#python dump_ims.py $INI $END

#eraland
#python dump_eraland.py $INI $END

python dump_isba.py /ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/2018/06/01/09/000/SURFOUT.20180601_12h00.nc

