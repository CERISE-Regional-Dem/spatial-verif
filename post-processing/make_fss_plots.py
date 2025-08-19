#!/usr/bin/env python

import pandas as pd
import sqlite3
from datetime import datetime
import os
import sys
from collections import OrderedDict
import numpy as np

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap


model="eraland"
year="2016"
this_period="May 2016"
date_ini = datetime(2016,5,1)
date_end = datetime(2016,5,15)
MET_res = f"/media/cap/extra_work/CERISE/MET_{model.upper()}_vs_IMS_winter_2015"
all_results = os.listdir(MET_res)
results = OrderedDict()
for f in all_results:
    
    if f.endswith("_cts.txt"):
        read_date = f.split("_")[3]
        results[read_date]  = pd.read_csv(os.path.join(MET_res,f),sep=r'\s+')
    elif f.endswith(".nc"):
        ncfile = f
    

# 
REGION = "FULL"
REGION_SEL="NORTH_SWEDEN"
hit_dict=OrderedDict()
for label in ["datetime","hit_rate"]:
    hit_dict[label] = []
for key_date in results.keys():
    df_sel = results[key_date][results[key_date]["VX_MASK"]  == REGION]
    hit_dict["hit_rate"].append(df_sel["PODY"].values[0])
    hit_dict["datetime"].append(datetime.strptime(df_sel["FCST_VALID_BEG"].values[0],"%Y%m%d_%H%M%S"))

# ### find fraction skill score

fss_files=OrderedDict()
for f in all_results:
    
    if f.endswith("_nbrcnt.txt"):
        read_date = f.split("_")[3]
        fss_files[read_date]  = pd.read_csv(os.path.join(MET_res,f),sep=r'\s+')
    
#date_sel = check_date
#get_fss_all = fss_files[date_sel][fss_files[date_sel]["VX_MASK"] == REGION]
#get_fss_nor_scan = fss_files[date_sel][fss_files[date_sel]["VX_MASK"] == REGION_SEL]
#fss_all = get_fss_all[["INTERP_PNTS","FSS","FCST_LEAD","FCST_VALID_BEG","FCST_VALID_END"]]
#fss_nor_scan = get_fss_nor_scan[["INTERP_PNTS","FSS","FCST_LEAD","FCST_VALID_BEG","FCST_VALID_END"]]


df_fss_full = pd.DataFrame(columns=["date","points","fss"])
df_fss_nor_scan = pd.DataFrame(columns=["date","points","fss"])


for key in fss_files:
    data = fss_files[key][fss_files[key]["VX_MASK"] == REGION]
    for _,r in data.iterrows():
        conv_date = datetime.strptime(r["FCST_VALID_BEG"],"%Y%m%d_%H%M%S")
        data_row = pd.DataFrame({"date":[conv_date],"points":[r["INTERP_PNTS"]],"fss":[r["FSS"]]},columns=["date","points","fss"])
        df_fss_full=pd.concat([df_fss_full,data_row],ignore_index=True)

for key in fss_files:
    data = fss_files[key][fss_files[key]["VX_MASK"] == REGION_SEL]
    for _,r in data.iterrows():
        conv_date = datetime.strptime(r["FCST_VALID_BEG"],"%Y%m%d_%H%M%S")
        data_row = pd.DataFrame({"date":[conv_date],"points":[r["INTERP_PNTS"]],"fss":[r["FSS"]]},columns=["date","points","fss"])
        df_fss_nor_scan=pd.concat([df_fss_nor_scan,data_row],ignore_index=True)


#this for plotting
df_fss_full["day"] = df_fss_full["date"].dt.strftime('%Y-%m-%d')
df_fss_nor_scan["day"] = df_fss_nor_scan["date"].dt.strftime('%Y-%m-%d')

#make some specific selections
#df_fss_nor_scan["day"] = df_fss_nor_scan["date"].dt.strftime('%Y-%m-%d')
#select = df_fss_full[(df_fss_full.date >= datetime(2016,5,1)) & (df_fss_full.date <= datetime(2016,5,15))]
#select = df_fss_nor_scan[(df_fss_nor_scan.date >= datetime(2015,11,1)) & (df_fss_full.date <= datetime(2015,11,15))]
#select = df_fss_nor_scan[(df_fss_nor_scan.date >= datetime(2016,5,1)) & (df_fss_full.date <= datetime(2016,5,15))]

select = df_fss_full[(df_fss_full.date >= date_ini) & (df_fss_full.date <= date_end)]
pivot_df = select.pivot(index='day', columns='points', values='fss')

from matplotlib.colors import LinearSegmentedColormap
# Create custom colormap (red to green)
colors = ['red', 'green']
n_bins = 10  # Number of color gradients
cmap = LinearSegmentedColormap.from_list("custom", colors, N=n_bins)


cmap = "coolwarm"
cmap = plt.cm.coolwarm.reversed()  # Inverted coolwarm
bounds = [0.5, 0.6,0.7, 0.8, 0.9,1.0]
norm = BoundaryNorm(bounds, ncolors=256)

#cmap = "viridis"
cmap = "coolwarm"
cmap = plt.cm.coolwarm.reversed()  # Inverted coolwarm
# Define the custom colormap (red to green)
#colors = ["#ff0000", "#ff8000", "#ffff00", "#80ff00", "#00ff00"]  # Red to green
#cmap = ListedColormap(colors)
#pivot_df = df_fss_full.pivot(index='day', columns='points', values='fss')

bounds = [0.5, 0.6,0.7, 0.8, 0.9,1.0]
norm = BoundaryNorm(bounds, ncolors=256)
# Plot the heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap=cmap,norm=norm)

plt.title(f'FSS Heatmap {model.upper()}, {this_period}')
plt.xlabel('Neighbourhood size')
plt.ylabel('Date')

plt.savefig(f'fss_heatmap_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()


# make a reduced version with a threshold
def plot_reduced():
    import matplotlib.colors as mcolors
    # Create a custom colormap with red for values < 0.5 and green for values >= 0.5
    colors = ['red', 'green']
    n_bins = 2  # We only want two colors
    custom_cmap = mcolors.LinearSegmentedColormap.from_list('custom', colors, N=n_bins)
    # Create the heatmap
    plt.figure(figsize=(12, 8))
    
    # Create a mask for values
    mask_high = pivot_df >= 0.7
    mask_low = pivot_df < 0.7

    # Create boundaries for the colormap
    bounds = [0, 0.7, 1]
    norm = mcolors.BoundaryNorm(bounds, custom_cmap.N)
    
    # Plot the heatmap with custom colormap
    sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap=custom_cmap,norm=norm,
                vmin=0, vmax=1,  # Set the range of values
                center=0.5)      # Set the center point for color transition
    
    plt.title('FSS Heatmap for CARRA1 vs IMS data, November 2015')
    plt.xlabel('Neighbourhood size')
    plt.ylabel('Date')
    plt.savefig(f'fss_heatmap_{model}_{year}.png', dpi=300, bbox_inches='tight')
    plt.show()
plot_reduced()

# Create a mask for values >= 0.5
#mask_high = pivot_df >= 0.6
#mask_low = pivot_df < 0.6
#
## Plot the heatmap with custom colormap
#sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap=custom_cmap,
#            vmin=0, vmax=1,  # Set the range of values
#            center=0.5)      # Set the center point for color transition
#
#plt.title('Two colors FSS Heatmap for {model.upper()} vs IMS data, selected region')
#plt.xlabel('Neighbourhood size')
#plt.ylabel('Date')
##plt.savefig(f'fss_heatmap_{model}_selected.png', dpi=300, bbox_inches='tight')
#plt.show()
