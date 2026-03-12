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
        'path': "/media/cap/extra_work/CERISE/MET_CERISE_vs_IMS_paper",
        'label': "CERISE",
        'color': '#1f77b4'  # Blue
    },
    'CARRA1': {
        'path': "/media/cap/extra_work/CERISE/MET_CARRA1_vs_IMS_paper",
        'label': "CARRA1", 
        'color': '#ff7f0e'  # Orange
    }
}

# Time period configuration
this_period = "2015-2019"
date_ini = datetime(2015, 9, 1)
date_end = datetime(2019, 9, 11)

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
        'full': load_fss_data(model_config['path'], REGION),
        'north_sweden': load_fss_data(model_config['path'], REGION_SEL)
    }

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
        # Filter to only winter months (Dec, Jan, Feb)
        df_filtered = df_filtered[df_filtered['date'].dt.month.isin([12,1,2])]
        filtered_data[model_name][region_key] = df_filtered



import pandas as pd
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

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
})

# Assuming you have your filtered_data dictionary from the original script
# Here's how to create enhanced visualizations:

def create_enhanced_comparisons(filtered_data, models, this_period):
    """Create multiple enhanced comparison plots"""
    
    # Method 1: Difference Plot (CARRA1 - CERISE)
    fig1, axes1 = plt.subplots(2, 2, figsize=(16, 10))
    fig1.suptitle(f'FSS Difference (CARRA1 - CERISE)\n{this_period}', 
                  fontsize=18, fontweight='bold')
    
    plot_configs = [
        ('full', 1, 0, 0, 'FULL Region - Scale 1'),
        ('full', 25, 0, 1, 'FULL Region - Scale 25'),
        ('north_sweden', 1, 1, 0, 'North Sweden - Scale 1'),
        ('north_sweden', 25, 1, 1, 'North Sweden - Scale 25')
    ]
    
    for region, scale, row, col, title in plot_configs:
        ax = axes1[row, col]
        
        # Get data for both models
        cerise_data = filtered_data['CERISE'][region]
        carra1_data = filtered_data['CARRA1'][region]
        
        cerise_scale = cerise_data[cerise_data['points'] == scale].sort_values('date')
        carra1_scale = carra1_data[carra1_data['points'] == scale].sort_values('date')
        
        # Merge on date to ensure alignment
        merged = pd.merge(cerise_scale[['date', 'fss']], 
                         carra1_scale[['date', 'fss']], 
                         on='date', suffixes=('_cerise', '_carra1'))
        
        if not merged.empty:
            difference = merged['fss_carra1'] - merged['fss_cerise']
            
            # Plot difference
            ax.plot(merged['date'], difference, 'g-', linewidth=2, alpha=0.7)
            ax.fill_between(merged['date'], 0, difference, 
                           where=(difference > 0), alpha=0.3, color='green', 
                           label='CARRA1 better')
            ax.fill_between(merged['date'], 0, difference, 
                           where=(difference < 0), alpha=0.3, color='red',
                           label='CERISE better')
            ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
            
            # Add statistics
            mean_diff = np.mean(difference)
            ax.text(0.02, 0.98, f'Mean Δ: {mean_diff:.4f}', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('FSS Difference')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
    
    plt.tight_layout()
    
    # Method 2: Box Plot Comparison
    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 10))
    fig2.suptitle(f'FSS Distribution Comparison\n{this_period}', 
                  fontsize=18, fontweight='bold')
    
    for region, scale, row, col, title in plot_configs:
        ax = axes2[row, col]
        
        cerise_data = filtered_data['CERISE'][region]
        carra1_data = filtered_data['CARRA1'][region]
        
        cerise_fss = cerise_data[cerise_data['points'] == scale]['fss']
        carra1_fss = carra1_data[carra1_data['points'] == scale]['fss']
        
        if not cerise_fss.empty and not carra1_fss.empty:
            box_data = [cerise_fss, carra1_fss]
            box_plot = ax.boxplot(box_data, labels=['CERISE', 'CARRA1'], 
                                 patch_artist=True)
            
            # Color the boxes
            box_plot['boxes'][0].set_facecolor('#1f77b4')
            box_plot['boxes'][1].set_facecolor('#ff7f0e')
            
            # Add statistical test
            statistic, p_value = stats.mannwhitneyu(carra1_fss, cerise_fss, 
                                                   alternative='two-sided')
            ax.text(0.02, 0.98, f'p-value: {p_value:.4f}', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(title)
        ax.set_ylabel('FSS')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Method 3: Cumulative Performance Plot
    fig3, axes3 = plt.subplots(2, 2, figsize=(16, 10))
    fig3.suptitle(f'Cumulative FSS Performance\n{this_period}', 
                  fontsize=18, fontweight='bold')
    
    for region, scale, row, col, title in plot_configs:
        ax = axes3[row, col]
        
        cerise_data = filtered_data['CERISE'][region]
        carra1_data = filtered_data['CARRA1'][region]
        
        cerise_scale = cerise_data[cerise_data['points'] == scale].sort_values('date')
        carra1_scale = carra1_data[carra1_data['points'] == scale].sort_values('date')
        
        if not cerise_scale.empty and not carra1_scale.empty:
            # Calculate cumulative mean
            cerise_cum_mean = cerise_scale['fss'].expanding().mean()
            carra1_cum_mean = carra1_scale['fss'].expanding().mean()
            
            ax.plot(cerise_scale['date'], cerise_cum_mean, 
                   color='#1f77b4', linewidth=2, label='CERISE')
            ax.plot(carra1_scale['date'], carra1_cum_mean, 
                   color='#ff7f0e', linewidth=2, label='CARRA1')
            
            # Highlight final values
            if len(cerise_cum_mean) > 0 and len(carra1_cum_mean) > 0:
                final_cerise = cerise_cum_mean.iloc[-1]
                final_carra1 = carra1_cum_mean.iloc[-1]
                ax.text(0.02, 0.02, 
                       f'Final: CERISE={final_cerise:.4f}, CARRA1={final_carra1:.4f}', 
                       transform=ax.transAxes,
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(title)
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Mean FSS')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        ax.legend()
    
    plt.tight_layout()
    
    # Method 4: Scatter Plot with Diagonal
    fig4, axes4 = plt.subplots(2, 2, figsize=(12, 10))
    fig4.suptitle(f'CERISE vs CARRA1 FSS Scatter\n{this_period}', 
                  fontsize=18, fontweight='bold')
    
    for region, scale, row, col, title in plot_configs:
        ax = axes4[row, col]
        
        cerise_data = filtered_data['CERISE'][region]
        carra1_data = filtered_data['CARRA1'][region]
        
        cerise_scale = cerise_data[cerise_data['points'] == scale]
        carra1_scale = carra1_data[carra1_data['points'] == scale]
        
        # Merge on date
        merged = pd.merge(cerise_scale[['date', 'fss']], 
                         carra1_scale[['date', 'fss']], 
                         on='date', suffixes=('_cerise', '_carra1'))
        
        if not merged.empty:
            ax.scatter(merged['fss_cerise'], merged['fss_carra1'], 
                      alpha=0.6, s=30)
            
            # Add diagonal line (perfect correlation)
            min_val = min(merged['fss_cerise'].min(), merged['fss_carra1'].min())
            max_val = max(merged['fss_cerise'].max(), merged['fss_carra1'].max())
            ax.plot([min_val, max_val], [min_val, max_val], 
                   'k--', alpha=0.5, label='Equal performance')
            
            # Calculate and display correlation
            corr = np.corrcoef(merged['fss_cerise'], merged['fss_carra1'])[0,1]
            
            # Count points above/below diagonal
            above_diag = (merged['fss_carra1'] > merged['fss_cerise']).sum()
            total_points = len(merged)
            
            ax.text(0.02, 0.98, 
                   f'r = {corr:.3f}\nCARRA1 > CERISE: {above_diag}/{total_points}', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        ax.set_title(title)
        ax.set_xlabel('CERISE FSS')
        ax.set_ylabel('CARRA1 FSS')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Make axes equal for better comparison
        ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    
    return fig1, fig2, fig3, fig4

# Method 5: Summary Statistics Table
def create_summary_table(filtered_data):
    """Create a summary statistics table"""
    
    summary_data = []
    
    for region_name, region_key in [('FULL', 'full'), ('North Sweden', 'north_sweden')]:
        for scale in [1, 25]:
            cerise_data = filtered_data['CERISE'][region_key]
            carra1_data = filtered_data['CARRA1'][region_key]
            
            cerise_fss = cerise_data[cerise_data['points'] == scale]['fss']
            carra1_fss = carra1_data[carra1_data['points'] == scale]['fss']
            
            if not cerise_fss.empty and not carra1_fss.empty:
                # Align data by merging on date
                cerise_scale = cerise_data[cerise_data['points'] == scale]
                carra1_scale = carra1_data[carra1_data['points'] == scale]
                merged = pd.merge(cerise_scale[['date', 'fss']], 
                                 carra1_scale[['date', 'fss']], 
                                 on='date', suffixes=('_cerise', '_carra1'))
                
                if not merged.empty:
                    mean_diff = np.mean(merged['fss_carra1'] - merged['fss_cerise'])
                    wins_carra1 = (merged['fss_carra1'] > merged['fss_cerise']).sum()
                    wins_cerise = (merged['fss_cerise'] > merged['fss_carra1']).sum()
                    total_comparisons = len(merged)
                    
                    summary_data.append({
                        'Region': region_name,
                        'Scale': scale,
                        'CERISE Mean': cerise_fss.mean(),
                        'CARRA1 Mean': carra1_fss.mean(),
                        'Mean Difference': mean_diff,
                        'CARRA1 Wins': f"{wins_carra1}/{total_comparisons}",
                        'CERISE Wins': f"{wins_cerise}/{total_comparisons}",
                        'Win Percentage CARRA1': f"{100*wins_carra1/total_comparisons:.1f}%",
                        'Win Percentage CERISE': f"{100*wins_cerise/total_comparisons:.1f}%"
                    })
    
    return pd.DataFrame(summary_data)

# Example usage (uncomment when you have your data):
#create_enhanced_comparisons(filtered_data, models, this_period)

# Generate all enhanced plots
fig1, fig2, fig3, fig4 = create_enhanced_comparisons(filtered_data, models, this_period)

# Save the enhanced plots
fig1.savefig('fss_difference_plot.pdf', dpi=300, bbox_inches='tight', 
             facecolor='white', edgecolor='none', format='pdf')
print("Saved: fss_difference_plot.pdf")

fig2.savefig('fss_boxplot_comparison.pdf', dpi=300, bbox_inches='tight',
             facecolor='white', edgecolor='none', format='pdf')
print("Saved: fss_boxplot_comparison.pdf")

fig3.savefig('fss_cumulative_performance.pdf', dpi=300, bbox_inches='tight',
             facecolor='white', edgecolor='none', format='pdf')
print("Saved: fss_cumulative_performance.pdf")

fig4.savefig('fss_scatter_comparison.pdf', dpi=300, bbox_inches='tight',
             facecolor='white', edgecolor='none', format='pdf')
print("Saved: fss_scatter_comparison.pdf")

# Show all plots
plt.show()



summary_table = create_summary_table(filtered_data)
print("Summary Statistics:")
print(summary_table.to_string(index=False))
