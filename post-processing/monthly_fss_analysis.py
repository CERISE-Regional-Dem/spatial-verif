#!/usr/bin/env python

import pandas as pd
from datetime import datetime
import os
from collections import OrderedDict
import numpy as np
import calendar

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import BoundaryNorm, ListedColormap

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

# Model configurations (colorblind-friendly palette)
models = {
    'CERISE': {
        'path': "/media/cap/extra_work/CERISE/MET_CERISE_vs_CRYO_paper",
        'label': "CERISE",
        'color': '#0072B2'  # Blue (colorblind-friendly)
    },
    'CARRA1': {
        'path': "/media/cap/extra_work/CERISE/MET_CARRA1_vs_CRYO_paper",
        'label': "CARRA1", 
        'color': '#D55E00'  # Vermillion (colorblind-friendly)
    }
}

# Time period configuration
this_period = "2015"
date_ini = datetime(2015, 10, 1)
date_end = datetime(2015, 12, 31)
regions  = ["full"] #,"north_scand"]

# Region configuration
REGION = "FULL"
#REGION_SEL = "NORTH_SWEDEN"
REGION_SEL = "NORTH_SCAND"

def load_fss_data(model_path, region):
    """Load FSS data for a specific model and region, avoiding concat warning."""
    all_results = os.listdir(model_path)
    fss_files = OrderedDict()
    # Load FSS files
    for f in all_results:
        if f.endswith("_nbrcnt.txt"):
            read_date = f.split("_")[3]
            fss_files[read_date] = pd.read_csv(os.path.join(model_path, f), sep=r'\s+')
    # Collect rows in a list
    rows = []
    for key in fss_files:
        data = fss_files[key][fss_files[key]["VX_MASK"] == region]
        for _, r in data.iterrows():
            conv_date = datetime.strptime(r["FCST_VALID_BEG"], "%Y%m%d_%H%M%S")
            rows.append({
                "date": conv_date,
                "points": r["INTERP_PNTS"],
                "fss": r["FSS"]
            })
    df_fss = pd.DataFrame(rows, columns=["date", "points", "fss"])
    return df_fss

def create_monthly_analysis_plots(df, model_name, region_name, year_month_str):
    """Create the extended FSS analysis plots for a specific month"""
    
    # Add day column for pivot
    df["day"] = df["date"].dt.strftime('%Y-%m-%d')
    
    # Create pivot table
    pivot_df = df.pivot(index='day', columns='points', values='fss')
    
    if pivot_df.empty:
        print(f"No data for {model_name} {region_name} {year_month_str}")
        return
    
    # Prepare data arrays
    scales = np.array(sorted(pivot_df.columns.values))
    days = list(pivot_df.index.values)
    fss = pivot_df.reindex(columns=scales).values
    
    # Create output directory
    output_dir = f"monthly_analysis_{model_name.lower()}_{region_name.lower()}"
    os.makedirs(output_dir, exist_ok=True)
    
    model_config = models[model_name]
    
    # 1) Heatmap
    plt.figure(figsize=(12, 8))
    cmap = plt.cm.coolwarm.reversed()
    bounds = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    norm = BoundaryNorm(bounds, ncolors=256)
    sns.heatmap(pivot_df, annot=True, fmt=".2f", cmap=cmap, norm=norm)
    plt.title(f'FSS Heatmap - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.xlabel('Neighbourhood Size (grid points)')
    plt.ylabel('Date')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/fss_heatmap_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2) FSS vs scale curves with median + IQR
    median = np.median(fss, axis=0)
    p25 = np.percentile(fss, 25, axis=0)
    p75 = np.percentile(fss, 75, axis=0)
    plt.figure(figsize=(8, 5))
    for i in range(fss.shape[0]):
        plt.plot(scales, fss[i, :], color='gray', alpha=0.25, linewidth=1)
    plt.plot(scales, median, color=model_config['color'], linewidth=3, label='Median')
    plt.fill_between(scales, p25, p75, color=model_config['color'], alpha=0.25, label='IQR')
    plt.ylim(0, 1.0)
    plt.xlabel('Neighbourhood Size (grid points)')
    plt.ylabel('FSS')
    plt.title(f'FSS vs Neighbourhood Size - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/fss_vs_scale_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3) Daily minimum scale to reach thresholds
    taus = [0.5, 0.7, 0.9]
    plt.figure(figsize=(10, 4))
    for tau in taus:
        min_scale = []
        for row in fss:
            idx = np.where(row >= tau)[0]
            min_scale.append(scales[idx[0]] if idx.size else np.nan)
        plt.plot(days, min_scale, marker='o', linestyle='-', label=f'τ={tau}')
    plt.ylabel('Min neighbourhood size to reach τ')
    plt.xlabel('Date')
    plt.title(f'Scale of Useful Skill - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/min_scale_time_series_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4) Distribution across days at each scale (boxplot)
    plt.figure(figsize=(9, 4))
    plt.boxplot([fss[:, j] for j in range(fss.shape[1])], positions=scales,
                widths=0.06*np.max(scales), showfliers=False)
    plt.plot(scales, np.mean(fss, axis=0), color=model_config['color'], 
             marker='o', linewidth=2, markersize=6, label='Mean')
    plt.ylim(0, 1.0)
    plt.xlabel('Neighbourhood Size (grid points)')
    plt.ylabel('FSS')
    plt.title(f'Distribution of Daily FSS per Scale - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/fss_boxplot_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5) Anomaly heatmap relative to scale median
    median_scale = np.median(fss, axis=0)
    anoms = fss - median_scale
    plt.figure(figsize=(12, 6))
    im = plt.imshow(anoms, aspect='auto', cmap='RdBu_r', vmin=-0.2, vmax=0.2,
                    extent=[scales[0], scales[-1], 0, len(days)])
    plt.colorbar(im, label='FSS anomaly vs scale median')
    plt.yticks(np.arange(len(days))+0.5, days)
    plt.xlabel('Neighbourhood Size (grid points)')
    plt.ylabel('Date')
    plt.title(f'FSS Anomalies - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/fss_anomaly_heatmap_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6) Average marginal gain with scale
    if fss.shape[1] > 1:  # Need at least 2 scales
        delta = np.diff(fss, axis=1)
        mean_delta = np.mean(delta, axis=0)
        plt.figure(figsize=(8, 4))
        plt.plot(scales[1:], mean_delta, marker='o', color=model_config['color'], 
                 linewidth=2, markersize=6)
        plt.axhline(0, color='k', linewidth=1)
        plt.xlabel('Neighbourhood Size (grid points)')
        plt.ylabel('Mean ΔFSS to next larger scale')
        plt.title(f'Average Skill Gain When Increasing Scale - {model_config["label"]} {region_name}\n{year_month_str}')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{output_dir}/fss_gain_vs_scale_{year_month_str.replace(" ", "_")}.pdf', 
                    dpi=300, bbox_inches='tight')
        plt.close()
    
    # 7) Fraction of days exceeding thresholds vs scale
    plt.figure(figsize=(8, 5))
    for t in taus:
        prop = np.mean(fss >= t, axis=0)
        plt.plot(scales, prop, marker='o', label=f'τ={t}', linewidth=2, markersize=6)
    plt.ylim(0, 1.0)
    plt.xlabel('Neighbourhood Size (grid points)')
    plt.ylabel('Fraction of days with FSS ≥ τ')
    plt.title(f'Skill Attainment vs Scale - {model_config["label"]} {region_name}\n{year_month_str}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/fss_attainment_{year_month_str.replace(" ", "_")}.pdf', 
                dpi=300, bbox_inches='tight')
    plt.close()

# Load data for both models and regions
print("Loading FSS data...")
model_data = {}
for model_name, model_config in models.items():
    print(f"Loading {model_name}...")
    model_data[model_name] = {
        'full': load_fss_data(model_config['path'], REGION)
        #'north_scand': load_fss_data(model_config['path'], REGION_SEL)
    }

# Filter data for the specified time period
filtered_data = {}
for model_name in models.keys():
    filtered_data[model_name] = {}
    for region_key in regions: #['full', 'north_part']:
        df = model_data[model_name][region_key]
        # Filter by date range
        df_filtered = df[
            (df.date >= date_ini) & 
            (df.date <= date_end)
        ].sort_values('date')
        # Filter to only winter months (Dec, Jan, Feb)
        print(f"Filtering for region: {region_key}")
        df_filtered = df_filtered[df_filtered['date'].dt.month.isin([11,12, 1, 2])]
        filtered_data[model_name][region_key] = df_filtered

# Generate monthly analysis plots
print("Generating monthly analysis plots...")
for model_name in models.keys():
    for region_key in regions: #['full', 'north_sweden']:
        region_name = 'FULL' if region_key == 'full' else 'North Scandinavia'
        df = filtered_data[model_name][region_key]
        
        if df.empty:
            print(f"No data for {model_name} {region_name}")
            continue
        
        # Group by year-month
        df['year_month'] = df['date'].dt.to_period('M')
        
        for year_month, month_data in df.groupby('year_month'):
            year_month_str = f"{calendar.month_name[year_month.month]} {year_month.year}"
            print(f"Processing {model_name} {region_name} {year_month_str}...")
            
            create_monthly_analysis_plots(
                month_data.copy(), 
                model_name, 
                region_name, 
                year_month_str
            )

print("Monthly FSS analysis complete!")
print("Check the generated directories for output files:")
for model_name in models.keys():
    for region_key in regions: #['full', 'north_sweden']:
        region_name = 'FULL' if region_key == 'full' else 'North Scandinavia'
        output_dir = f"monthly_analysis_{model_name.lower()}_{region_name.lower().replace(' ', '_')}"
        print(f"  - {output_dir}/")
