#!/usr/bin/env bash

#not sure which one is important, but loading the library
# did not work with the script. Not using metview here
#export METVIEW_PYTHON_START_TIMEOUT=10
#export METVIEW_PYTHON_START_CMD=metview
#export METVIEW_PYTHON_ONLY=1


NBOOK=cerise_fss_nuuk.qmd
#create the html
quarto preview $NBOOK --no-browser --no-watch-inputs

#can also use
#quarto render $NBOOK 


#convert to ipynb
#quarto convert $NBOOK
