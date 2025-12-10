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
year="2015_2019"
this_period="2015-2019"
date_ini = datetime(2015,9,1)
date_end = datetime(2019,9,11)
MET_res = f"/media/cap/extra_work/CERISE/MET_CERISE_vs_IMS_paper"
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

# Filter data for the specified time period
select_full = df_fss_full[(df_fss_full.date >= date_ini) & (df_fss_full.date <= date_end)]
select_nor_scan = df_fss_nor_scan[(df_fss_nor_scan.date >= date_ini) & (df_fss_nor_scan.date <= date_end)]

# Create time series plots for FSS values at points 1 and 25
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle(f'FSS Time Series\n{model_label.upper()} Model Performance, {this_period}', 
             fontsize=18, fontweight='bold', y=0.98)

# Define colors for different point values
colors = {'1': '#1f77b4', '25': '#ff7f0e'}  # Blue for 1 point, Orange for 25 points

# Plot 1: df_fss_full with points=1
ax1 = axes[0, 0]
data_1_full = select_full[select_full['points'] == 1].sort_values('date')
if not data_1_full.empty:
    ax1.plot(data_1_full['date'], data_1_full['fss'], 
             color=colors['1'], linewidth=2, marker='o', markersize=4, 
             label='1 grid point', alpha=0.8)
ax1.set_title('FULL Region - 1 Grid Point', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
ax1.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45, labelsize=10)
ax1.set_ylim(0.5, 1.0)

# Plot 2: df_fss_full with points=25
ax2 = axes[0, 1]
data_25_full = select_full[select_full['points'] == 25].sort_values('date')
if not data_25_full.empty:
    ax2.plot(data_25_full['date'], data_25_full['fss'], 
             color=colors['25'], linewidth=2, marker='s', markersize=4, 
             label='25 grid points', alpha=0.8)
ax2.set_title('FULL Region - 25 Grid Points', fontsize=14, fontweight='bold')
ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=45, labelsize=10)
ax2.set_ylim(0.5, 1.0)

# Plot 3: df_fss_nor_scan with points=1
ax3 = axes[1, 0]
data_1_nor = select_nor_scan[select_nor_scan['points'] == 1].sort_values('date')
if not data_1_nor.empty:
    ax3.plot(data_1_nor['date'], data_1_nor['fss'], 
             color=colors['1'], linewidth=2, marker='o', markersize=4, 
             label='1 grid point', alpha=0.8)
ax3.set_title('North Sweden Region - 1 Grid Point', fontsize=14, fontweight='bold')
ax3.set_xlabel('Date', fontsize=12, fontweight='bold')
ax3.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.tick_params(axis='x', rotation=45, labelsize=10)
ax3.set_ylim(0.5, 1.0)

# Plot 4: df_fss_nor_scan with points=25
ax4 = axes[1, 1]
data_25_nor = select_nor_scan[select_nor_scan['points'] == 25].sort_values('date')
if not data_25_nor.empty:
    ax4.plot(data_25_nor['date'], data_25_nor['fss'], 
             color=colors['25'], linewidth=2, marker='s', markersize=4, 
             label='25 grid points', alpha=0.8)
ax4.set_title('North Sweden Region - 25 Grid Points', fontsize=14, fontweight='bold')
ax4.set_xlabel('Date', fontsize=12, fontweight='bold')
ax4.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.tick_params(axis='x', rotation=45, labelsize=10)
ax4.set_ylim(0.5, 1.0)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(top=0.92)

# Save the figure
plt.savefig(f'fss_timeseries_{model}_publication.pdf', 
            dpi=300, 
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none',
            format='pdf')

plt.show()

# Optional: Create a combined plot showing both point values on the same axes
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))
fig2.suptitle(f'FSS Time Series Comparison\n{model_label.upper()} Model Performance, {this_period}', 
              fontsize=18, fontweight='bold', y=0.98)

# Combined plot for FULL region
ax_full = axes2[0]
if not data_1_full.empty:
    ax_full.plot(data_1_full['date'], data_1_full['fss'], 
                 color=colors['1'], linewidth=2, marker='o', markersize=4, 
                 label='1 grid point', alpha=0.8)
if not data_25_full.empty:
    ax_full.plot(data_25_full['date'], data_25_full['fss'], 
                 color=colors['25'], linewidth=2, marker='s', markersize=4, 
                 label='25 grid points', alpha=0.8)
ax_full.set_title('FULL Region', fontsize=14, fontweight='bold')
ax_full.set_xlabel('Date', fontsize=12, fontweight='bold')
ax_full.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax_full.grid(True, alpha=0.3)
ax_full.tick_params(axis='x', rotation=45, labelsize=10)
ax_full.set_ylim(0.5, 1.0)
ax_full.legend()

# Combined plot for North Sweden region
ax_nor = axes2[1]
if not data_1_nor.empty:
    ax_nor.plot(data_1_nor['date'], data_1_nor['fss'], 
                color=colors['1'], linewidth=2, marker='o', markersize=4, 
                label='1 grid point', alpha=0.8)
if not data_25_nor.empty:
    ax_nor.plot(data_25_nor['date'], data_25_nor['fss'], 
                color=colors['25'], linewidth=2, marker='s', markersize=4, 
                label='25 grid points', alpha=0.8)
ax_nor.set_title('North Sweden Region', fontsize=14, fontweight='bold')
ax_nor.set_xlabel('Date', fontsize=12, fontweight='bold')
ax_nor.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax_nor.grid(True, alpha=0.3)
ax_nor.tick_params(axis='x', rotation=45, labelsize=10)
ax_nor.set_ylim(0.5, 1.0)
ax_nor.legend()

plt.tight_layout()
plt.subplots_adjust(top=0.90)

# Save the combined figure
plt.savefig(f'fss_timeseries_combined_{model}_publication.pdf', 
            dpi=300, 
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none',
            format='pdf')

plt.show()
