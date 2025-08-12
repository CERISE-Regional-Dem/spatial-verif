# spatial-verif
Spatial verification scripts

## libraries used
- [harp](https://harphub.github.io/harp/). For installation instructions follow this guide: [INSTALLATION.md](https://github.com/harphub/oper-harp-verif/tree/master/ACCORD_VS_202406) document.
- [cdo](https://code.mpimet.mpg.de/projects/cdo)
- [nco](https://nco.sourceforge.net/)
- [Model Evaluation Tools](https://met.readthedocs.io/en/latest/Users_Guide/overview.html), using version 11.



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
