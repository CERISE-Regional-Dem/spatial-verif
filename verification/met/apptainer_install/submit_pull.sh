#!/usr/bin/env bash
#SBATCH --mem-per-cpu=16GB
#SBATCH --time=48:00:00

ml apptainer
[ ! -d $SCRATCH/apptainer/cache ] && mkdir $SCRATCH/apptainer/cache
[ ! -d $SCRATCH/apptainer/tmpdir ] && mkdir $SCRATCH/apptainer/tmpdir

export APPTAINER_CACHEDIR=$SCRATCH/apptainer/cache
export APPTAINER_TMPDIR=$SCRATCH/apptainer/tmpdir
apptainer pull docker://dtcenter/met:12.1.0
