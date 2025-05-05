#!/usr/bin/env bash

MODE=/perm/nhd/MET/bin/mode_analysis

#/ec/res4/scratch/nhd/CERISE/MET_CARRA1_vs_IMS_winter_2015/mode_000000L_20151101_060000V_000000A_obj.txt
datapath=$SCRATCH/CERISE/MET_CARRA1_vs_IMS_winter_2015
$MODE \
    -lookin ${datapath}/mode_000000L_20151101_060000V_000000A_obj.txt \
    -summary \
    -column AREA -column LENGTH -column WIDTH -column AREA -column CURVATURE -column INTENSITY_90 \
    -fcst -single \
    -dump_row job_summary_test.txt \
    -out      job_summary_analysis.out -v 6
