#!/usr/bin/env python

import pandas as pd
from datetime import datetime
import os
from collections import OrderedDict
import numpy as np

import matplotlib.pyplot as plt

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
    'text.usetex': False,
    'mathtext.fontset': 'stix'
})

# Model configurations
models = {
    'CERISE': {
        'path': "/media/cap/extra_work/CERISE/MET_CERISE_vs_CRYO_selection",
        'label': "CERISE",
        'color': '#1f77b4'  # Blue
    },
    'CARRA1': {
        'path': "/media/cap/extra_work/CERISE/MET_CARRA1_vs_CRYO_selection",
        'label': "CARRA1", 
        'color': '#ff7f0e'  # Orange
    }
}

# Time period configuration
this_period = "2015"
date_ini = datetime(2015, 10, 1)
date_end = datetime(2015, 12, 31)

# Region configuration
REGION = "FULL"
REGION_SEL = "NORTH_SWEDEN"

def load_fss_data(model_path, region):
    """Load FSS data for a specific model and region"""
    all_results = os.listdir(model_path)
    fss_files = OrderedDict()
    
    # Load FSS files
    for f in all_results:
        if f.endswith("_nbrcnt.txt"):
            read_date = f.split("_")[3]
            fss_files[read_date] = pd.read_csv(os.path.join(model_path, f), sep=r'\s+')
    
    # Create dataframe
    df_fss = pd.DataFrame(columns=["date", "points", "fss"])
    
    for key in fss_files:
        data = fss_files[key][fss_files[key]["VX_MASK"] == region]
        for _, r in data.iterrows():
            conv_date = datetime.strptime(r["FCST_VALID_BEG"], "%Y%m%d_%H%M%S")
            data_row = pd.DataFrame({
                "date": [conv_date],
                "points": [r["INTERP_PNTS"]],
                "fss": [r["FSS"]]
            }, columns=["date", "points", "fss"])
            df_fss = pd.concat([df_fss, data_row], ignore_index=True)
    return df_fss

# Load data for both models and regions
model_data = {}
for model_name, model_config in models.items():
    model_data[model_name] = {
        'full': load_fss_data(model_config['path'], REGION)
        #'north_sweden': load_fss_data(model_config['path'], REGION_SEL)
    }

import pdb
pdb.set_trace()
# Filter data for the specified time period and extract relevant scales (points 1 and 25)
scales_to_plot = [1, 25]
filtered_data = {}

for model_name in models.keys():
    filtered_data[model_name] = {}
    for region_key in ['full', 'north_sweden']:
        df = model_data[model_name][region_key]
        # Filter by date range and scales
        df_filtered = df[
            (df.date >= date_ini) & 
            (df.date <= date_end) & 
            (df.points.isin(scales_to_plot))
        ].sort_values('date')
        filtered_data[model_name][region_key] = df_filtered

# Create comparison plots
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
fig.suptitle(f'FSS Time Series Comparison\nModel Performance, {this_period}', 
             fontsize=18, fontweight='bold', y=0.98)

# Define markers for different scales
markers = {1: 'o', 25: 's'}
scale_labels = {1: 'Scale 1', 25: 'Scale 25'}

# Plot 1: FULL Region - Scale 1
ax1 = axes[0, 0]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['full']
    data_scale_1 = data[data['points'] == 1]
    if not data_scale_1.empty:
        ax1.plot(data_scale_1['date'], data_scale_1['fss'], 
                 color=model_config['color'], linewidth=2, 
                 marker=markers[1], markersize=4, 
                 label=model_config['label'], alpha=0.8)

ax1.set_title('FULL Region - Scale 1', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
ax1.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.tick_params(axis='x', rotation=45, labelsize=10)
ax1.set_ylim(0.1, 1.0)
ax1.legend()

# Plot 2: FULL Region - Scale 25
ax2 = axes[0, 1]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['full']
    data_scale_25 = data[data['points'] == 25]
    if not data_scale_25.empty:
        ax2.plot(data_scale_25['date'], data_scale_25['fss'], 
                 color=model_config['color'], linewidth=2, 
                 marker=markers[25], markersize=4, 
                 label=model_config['label'], alpha=0.8)

ax2.set_title('FULL Region - Scale 25', fontsize=14, fontweight='bold')
ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
ax2.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)
ax2.tick_params(axis='x', rotation=45, labelsize=10)
ax2.set_ylim(0.1, 1.0)
ax2.legend()

# Plot 3: North Sweden Region - Scale 1
ax3 = axes[1, 0]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['north_sweden']
    data_scale_1 = data[data['points'] == 1]
    if not data_scale_1.empty:
        ax3.plot(data_scale_1['date'], data_scale_1['fss'], 
                 color=model_config['color'], linewidth=2, 
                 marker=markers[1], markersize=4, 
                 label=model_config['label'], alpha=0.8)

ax3.set_title('North Sweden Region - Scale 1', fontsize=14, fontweight='bold')
ax3.set_xlabel('Date', fontsize=12, fontweight='bold')
ax3.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax3.grid(True, alpha=0.3)
ax3.tick_params(axis='x', rotation=45, labelsize=10)
ax3.set_ylim(0.1, 1.0)
ax3.legend()

# Plot 4: North Sweden Region - Scale 25
ax4 = axes[1, 1]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['north_sweden']
    data_scale_25 = data[data['points'] == 25]
    if not data_scale_25.empty:
        ax4.plot(data_scale_25['date'], data_scale_25['fss'], 
                 color=model_config['color'], linewidth=2, 
                 marker=markers[25], markersize=4, 
                 label=model_config['label'], alpha=0.8)

ax4.set_title('North Sweden Region - Scale 25', fontsize=14, fontweight='bold')
ax4.set_xlabel('Date', fontsize=12, fontweight='bold')
ax4.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3)
ax4.tick_params(axis='x', rotation=45, labelsize=10)
ax4.set_ylim(0.1, 1.0)
ax4.legend()

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(top=0.92)

# Save the figure
plt.savefig('fss_timeseries_model_comparison.pdf', 
            dpi=300, 
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none',
            format='pdf')

plt.show()

# Create a simplified comparison plot with both scales on same axes
fig2, axes2 = plt.subplots(1, 2, figsize=(16, 6))
fig2.suptitle(f'FSS Model Comparison by Scale\n{this_period}', 
              fontsize=18, fontweight='bold', y=0.98)

# Combined plot for FULL region
ax_full = axes2[0]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['full']
    for scale in scales_to_plot:
        data_scale = data[data['points'] == scale]
        if not data_scale.empty:
            linestyle = '-' if scale == 1 else '--'
            ax_full.plot(data_scale['date'], data_scale['fss'], 
                         color=model_config['color'], linewidth=2, 
                         marker=markers[scale], markersize=4, 
                         linestyle=linestyle,
                         label=f"{model_config['label']} - {scale_labels[scale]}", 
                         alpha=0.8)

ax_full.set_title('FULL Region', fontsize=14, fontweight='bold')
ax_full.set_xlabel('Date', fontsize=12, fontweight='bold')
ax_full.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax_full.grid(True, alpha=0.3)
ax_full.tick_params(axis='x', rotation=45, labelsize=10)
ax_full.set_ylim(0.1, 1.0)
ax_full.legend()

# Combined plot for North Sweden region
ax_nor = axes2[1]
for model_name, model_config in models.items():
    data = filtered_data[model_name]['north_sweden']
    for scale in scales_to_plot:
        data_scale = data[data['points'] == scale]
        if not data_scale.empty:
            linestyle = '-' if scale == 1 else '--'
            ax_nor.plot(data_scale['date'], data_scale['fss'], 
                        color=model_config['color'], linewidth=2, 
                        marker=markers[scale], markersize=4, 
                        linestyle=linestyle,
                        label=f"{model_config['label']} - {scale_labels[scale]}", 
                        alpha=0.8)

ax_nor.set_title('North Sweden Region', fontsize=14, fontweight='bold')
ax_nor.set_xlabel('Date', fontsize=12, fontweight='bold')
ax_nor.set_ylabel('FSS', fontsize=12, fontweight='bold')
ax_nor.grid(True, alpha=0.3)
ax_nor.tick_params(axis='x', rotation=45, labelsize=10)
ax_nor.set_ylim(0.1, 1.0)
ax_nor.legend()

plt.tight_layout()
plt.subplots_adjust(top=0.90)

# Save the combined figure
plt.savefig('fss_timeseries_combined_comparison.pdf', 
            dpi=300, 
            bbox_inches='tight',
            facecolor='white',
            edgecolor='none',
            format='pdf')

plt.show()
