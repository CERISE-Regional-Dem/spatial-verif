# spatial-verif
Spatial verification scripts

## libraries used
- [harp](https://harphub.github.io/harp/). For installation instructions follow this guide: [INSTALLATION.md](https://github.com/harphub/oper-harp-verif/tree/master/ACCORD_VS_202406) document.
- [cdo](https://code.mpimet.mpg.de/projects/cdo)
- [nco](https://nco.sourceforge.net/)
- [Model Evaluation Tools](https://met.readthedocs.io/en/latest/Users_Guide/overview.html), using version 11.
- [Apptainer](https://apptainer.org/) for using MET without need to compile the source code.


### Install python env (atos)
```
module load python3/3.10.10-01
python3 -m venv .venv
pip install -r requirements.txt
```

## alternatively, using uv (atos)
```
module load uv
uv venv .venv --python 3.10
source .venv/bin/activate
uv pip install -r requirements
uv cache clean
```

## Installing MET
Refer to the MET guides for [compilation instructions](https://dtcenter.org/met-online-tutorial-metv6-1/tutorial-setup/compilation).

Alternatively, in atos, it is possible to use a containarized version of MET tools, using apptainer
In atos, run the script (also included [here](verification/met/apptainer_install)):

```
#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=48:00:00

ml apptainer
[ ! -d $SCRATCH/apptainer/cache ] && mkdir $SCRATCH/apptainer/cache
[ ! -d $SCRATCH/apptainer/tmpdir ] && mkdir $SCRATCH/apptainer/tmpdir

export APPTAINER_CACHEDIR=$SCRATCH/apptainer/cache
export APPTAINER_TMPDIR=$SCRATCH/apptainer/tmpdir
apptainer pull docker://dtcenter/met:12.1.0

```
This will create the file:

`met_12.1.0.sif`

Which can then be used in the verification process to call the MET binaries (in particular `grid_stat`)
Example script can be found in `spatial-verif/verification/met/verify_carra1_land2_cryo.sh`.
To test the installation, run:
```
ml apptainer
apptainer run /path_to_binary/met_12.1.0.sif grid_stat
``` 

