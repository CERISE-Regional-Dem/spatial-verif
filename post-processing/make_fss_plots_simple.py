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
model="CARRA1_LAND2"
year="2016"
this_period="2015"
max_points = 121  # Maximum number of neighbourhood points to include in heatmap
date_ini = datetime(2015,10,15)
date_end = datetime(2015,11,29)
#MET_res = f"/media/cap/extra_work/CERISE/MET_{model.upper()}_vs_IMS_winter_2015"
MET_res = f"/media/cap/extra_work/CERISE/MET_{model}_CRYO"

all_results = os.listdir(MET_res)
results = OrderedDict()
for f in all_results:
    
    if f.endswith("_cts.txt"):
        read_date = f.split("_")[3]
        print(f"Reading {f}")
        results[read_date]  = pd.read_csv(os.path.join(MET_res,f),sep=r'\s+')

    elif f.endswith(".nc"):
        ncfile = f
    

# 
REGION = "FULL"
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

print("\n=== DEBUG: Processing FSS files ===")
for key in fss_files:
    data = fss_files[key][fss_files[key]["VX_MASK"] == REGION]
    print(f"Date key: {key}, Number of rows: {len(data)}")
    for _,r in data.iterrows():
        conv_date = datetime.strptime(r["FCST_VALID_BEG"],"%Y%m%d_%H%M%S")
        fss_value = r["FSS"]
        points_value = r["INTERP_PNTS"]
        print(f"  Date: {conv_date}, Points: {points_value}, FSS: {fss_value}, FSS is NaN: {pd.isna(fss_value)}")
        data_row = pd.DataFrame({"date":[conv_date],"points":[points_value],"fss":[fss_value]},columns=["date","points","fss"])
        df_fss_full=pd.concat([df_fss_full,data_row],ignore_index=True)

print(f"\n=== DEBUG: Total rows in df_fss_full: {len(df_fss_full)} ===")
print(f"Unique dates: {df_fss_full['date'].nunique()}")
print(f"Unique points: {sorted(df_fss_full['points'].unique())}")
print(f"FSS NaN count: {df_fss_full['fss'].isna().sum()}")

df_fss_full["day"] = df_fss_full["date"].dt.strftime('%Y-%m-%d')

print(f"\n=== DEBUG: Filtering data between {date_ini} and {date_end} ===")
select = df_fss_full[(df_fss_full.date >= date_ini) & (df_fss_full.date <= date_end)]
print(f"Rows after date filter: {len(select)}")
print(f"Unique days after filter: {select['day'].nunique()}")
print(f"Unique points after filter: {sorted(select['points'].unique())}")

print(f"\n=== DEBUG: Filtering points <= {max_points} ===")
select = select[select['points'] <= max_points]
print(f"Rows after points filter: {len(select)}")
print(f"Unique points after points filter: {sorted(select['points'].unique())}")

print("\n=== DEBUG: Creating pivot table ===")
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
bounds = [0.5, 0.6,0.7, 0.8, 0.9,1.0]
norm = BoundaryNorm(bounds, ncolors=256)
# Plot the heatmap
plt.figure(figsize=(12, 8))
mask = pivot_df.isna()
sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap=cmap, norm=norm, mask=False, cbar_kws={'label': 'FSS'})
for i in range(len(pivot_df)):
    for j in range(len(pivot_df.columns)):
        if mask.iloc[i, j]:
            plt.text(j + 0.5, i + 0.5, 'N/A', ha='center', va='center', color='black')

plt.title(f'FSS Heatmap {model.upper()}, {this_period}')
plt.xlabel('Neighbourhood size')
plt.ylabel('Date')

plt.savefig(f'fss_heatmap_{model}_{year}.png', dpi=300, bbox_inches='tight')
plt.show()

