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
import matplotlib.patches as patches

# Set publication-quality style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['Times New Roman'],
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 12,
    'ytick.labelsize': 12,
    'legend.fontsize': 12,
    'figure.titlesize': 18,
    'axes.linewidth': 1.2,
    'grid.linewidth': 0.8,
    'lines.linewidth': 2,
    'patch.linewidth': 1.2,
    'xtick.major.width': 1.2,
    'ytick.major.width': 1.2,
    'xtick.minor.width': 0.8,
    'ytick.minor.width': 0.8,
    'text.usetex': False,  # Set to True if you have LaTeX installed
    'mathtext.fontset': 'stix'
})

model="CERISE"
model_label="CERISE"
year="2015"
this_period="November 2015"
date_ini = datetime(2015,11,1)
date_end = datetime(2015,11,15)
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

select = df_fss_full[(df_fss_full.date >= date_ini) & (df_fss_full.date <= date_end)]
pivot_df = select.pivot(index='day', columns='points', values='fss')

# Create publication-quality figure
fig, ax = plt.subplots(figsize=(14, 10))

# Define professional colormap and normalization
cmap = plt.cm.RdYlGn  # Red-Yellow-Green colormap (better for FSS interpretation)
bounds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
norm = BoundaryNorm(bounds, ncolors=256)

# Create the heatmap with enhanced styling
heatmap = sns.heatmap(pivot_df, 
                     annot=True, 
                     fmt=".3f",  # More precision for publication
                     cmap=cmap,
                     norm=norm,
                     cbar_kws={
                         'label': 'Fraction Skill Score (FSS)',
                         'shrink': 0.8,
                         'aspect': 30,
                         'pad': 0.02
                     },
                     linewidths=0.5,
                     linecolor='white',
                     square=False,
                     annot_kws={'size': 11, 'weight': 'bold'},
                     ax=ax)

# Enhance the plot appearance
ax.set_title(f'FSS Heatmap\n{model_label.upper()} Model Performance, {this_period}', 
             fontsize=18, fontweight='bold', pad=20)
ax.set_xlabel('Neighbourhood Size (grid points)', fontsize=14, fontweight='bold')
ax.set_ylabel('Date', fontsize=14, fontweight='bold')

# Improve tick labels
ax.tick_params(axis='x', rotation=45, labelsize=12)
ax.tick_params(axis='y', rotation=0, labelsize=12)

# Format y-axis dates for better readability
y_labels = [label.get_text() for label in ax.get_yticklabels()]
formatted_labels = [datetime.strptime(label, '%Y-%m-%d').strftime('%b %d') for label in y_labels if label]
ax.set_yticklabels(formatted_labels, rotation=0)

# Add a subtle border around the heatmap
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1.5)
    spine.set_color('black')

# Adjust colorbar
cbar = heatmap.collections[0].colorbar
cbar.ax.tick_params(labelsize=12)
cbar.set_label('Fraction Skill Score (FSS)', fontsize=14, fontweight='bold')

# Add grid for better readability
ax.grid(False)  # Turn off seaborn grid
ax.set_axisbelow(True)

# Tight layout for better spacing
plt.tight_layout()

# Save with high quality settings
plt.savefig(f'fss_heatmap_{model}_{year}_publication.pdf', 
           dpi=300, 
           bbox_inches='tight',
           facecolor='white',
           edgecolor='none',
           format='pdf')

plt.savefig(f'fss_heatmap_{model}_{year}_publication.png', 
           dpi=300, 
           bbox_inches='tight',
           facecolor='white',
           edgecolor='none',
           format='png')

plt.show()
