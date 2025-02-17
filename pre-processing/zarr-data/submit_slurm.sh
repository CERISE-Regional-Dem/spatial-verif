#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate

cd /ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/zarr-data
INI="2015-11-01"
END="2015-12-31"
#CERISE
#python dump_cerise.py $INI $END

#CARRA1
#python dump_carra1.py $INI $END
#IMS
#python dump_ims.py $INI $END

#eraland
python dump_eraland.py $INI $END

