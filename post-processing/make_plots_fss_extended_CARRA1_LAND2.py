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


model="CARRA1_LAND2"
year="2015"
this_period="Oct 2015"
date_ini = datetime(2015,10,15)
date_end = datetime(2015,10,31)
MET_res = "/media/cap/extra_work/CERISE/MET_CARRA1_LAND2_CRYO"
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
#df_fss_nor_scan["day"] = df_fss_nor_scan["date"].dt.strftime('%Y-%m-%d')

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

# Build arrays for additional visualizations
# Prepare scales and days in consistent order
scales = np.array(sorted(pivot_df.columns.values))
days = list(pivot_df.index.values)
# fss matrix with shape (n_days, n_scales)
fss = pivot_df.reindex(columns=scales).values

# 1) FSS vs scale curves with median + IQR
median = np.median(fss, axis=0)
p25 = np.percentile(fss, 25, axis=0)
p75 = np.percentile(fss, 75, axis=0)
plt.figure(figsize=(8,5))
for i in range(fss.shape[0]):
    plt.plot(scales, fss[i, :], color='gray', alpha=0.25, linewidth=1)
plt.plot(scales, median, color='black', linewidth=2, label='Median')
plt.fill_between(scales, p25, p75, color='steelblue', alpha=0.25, label='IQR')
plt.ylim(0, 1.0)
plt.xlabel('Neighbourhood size')
plt.ylabel('FSS')
plt.title(f'FSS vs Neighbourhood Size — {this_period}')
plt.legend()
plt.tight_layout()
plt.savefig(f'fss_vs_scale_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

# 2) Daily minimum scale to reach thresholds
taus = [0.5, 0.7, 0.9]
plt.figure(figsize=(10,4))
for tau in taus:
    min_scale = []
    for row in fss:
        idx = np.where(row >= tau)[0]
        min_scale.append(scales[idx[0]] if idx.size else np.nan)
    plt.plot(days, min_scale, marker='o', linestyle='-', label=f'τ={tau}')
plt.ylabel('Min neighbourhood size to reach τ')
plt.xlabel('Date')
plt.title(f'Scale of useful skill — {this_period}')
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'min_scale_time_series_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

# 3) Distribution across days at each scale (boxplot)
plt.figure(figsize=(9,4))
plt.boxplot([fss[:, j] for j in range(fss.shape[1])], positions=scales,
            widths=0.06*np.max(scales), showfliers=False)
plt.plot(scales, np.mean(fss, axis=0), color='black', marker='o', label='Mean')
plt.ylim(0, 1.0)
plt.xlabel('Neighbourhood size')
plt.ylabel('FSS')
plt.title(f'Distribution of daily FSS per scale — {this_period}')
plt.legend()
plt.tight_layout()
plt.savefig(f'fss_boxplot_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

# 4) Anomaly heatmap relative to scale median
median_scale = np.median(fss, axis=0)
anoms = fss - median_scale
plt.figure(figsize=(12, 6))
im = plt.imshow(anoms, aspect='auto', cmap='RdBu_r', vmin=-0.2, vmax=0.2,
                extent=[scales[0], scales[-1], 0, len(days)])
plt.colorbar(im, label='FSS anomaly vs scale median')
plt.yticks(np.arange(len(days))+0.5, days)
plt.xlabel('Neighbourhood size')
plt.ylabel('Date')
plt.title(f'FSS anomalies — {this_period}')
plt.tight_layout()
plt.savefig(f'fss_anomaly_heatmap_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

# 5) Average marginal gain with scale
delta = np.diff(fss, axis=1)
mean_delta = np.mean(delta, axis=0)
plt.figure(figsize=(8,4))
plt.plot(scales[1:], mean_delta, marker='o')
plt.axhline(0, color='k', linewidth=1)
plt.xlabel('Neighbourhood size')
plt.ylabel('Mean ΔFSS to next larger scale')
plt.title(f'Average skill gain when increasing scale — {this_period}')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'fss_gain_vs_scale_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

# 6) Fraction of days exceeding thresholds vs scale
plt.figure(figsize=(8,5))
for t in taus:
    prop = np.mean(fss >= t, axis=0)
    plt.plot(scales, prop, marker='o', label=f'τ={t}')
plt.ylim(0, 1.0)
plt.xlabel('Neighbourhood size')
plt.ylabel('Fraction of days with FSS ≥ τ')
plt.title(f'Skill attainment vs scale — {this_period}')
plt.legend()
plt.tight_layout()
plt.savefig(f'fss_attainment_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()
