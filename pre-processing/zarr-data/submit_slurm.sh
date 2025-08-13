#!/usr/bin/env bash
#SBATCH --mem-per-cpu=64GB
#SBATCH --time=48:00:00

#activate python env
source /ec/res4/scratch/nhd/CERISE/cerise_snow_verif/.venv/bin/activate
OUTDIR=/ec/res4/scratch/nhd/CERISE/amsr2_test
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
for day in $(seq -w 1 30); do
#python dump_isba.py /ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/2018/06/30/00/000/SURFOUT.20180630_03h00.nc
python dump_isba.py /ec/res4/hpcperm/nhd/verification/CERISE/amsr2_test/2018/06/$day/00/000/SURFOUT.201806${day}_03h00.nc $OUTDIR
exit
done

