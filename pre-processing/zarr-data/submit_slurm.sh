#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate

cd /ec/res4/scratch/nhd/CERISE/spatial-verif/pre-processing/zarr-data

#CERISE
#python dump_cerise.py

#CARRA1
python dump_carra1.py
#IMS
#python dump_ims.py
