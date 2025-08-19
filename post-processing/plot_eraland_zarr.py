import xarray as xr
import numpy as np
import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import matplotlib.pyplot as plt

import sys
date_selected = str(sys.argv[1]) # "2016-09-01"





def get_ana_areadef():
    ana = xr.open_zarr(f"/scratch/fab0/Projects/cerise/carra_snow_data/ana_v2.zarr")
    proj_dict = ccrs.Projection(
        proj4_params=ana.projection,
    ).to_dict()
    proj = pyproj.Proj(proj_dict)
    return pyresample.geometry.AreaDefinition(
        "model domain",
        "1",
        "1",
        projection=proj_dict,
        width=ana.x.size,
        height=ana.y.size,
        area_extent=ana.bounding_box,
    )

def map_field(field, ax, **kwargs):
    import cartopy.feature as cfeature
    ax.coastlines(resolution='50m', color='black', linewidth=1)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    return ax.imshow(field,
                  transform=crs,
                  extent=crs.bounds,
                  zorder=0,
                  **kwargs)


area_def = get_ana_areadef()
crs = area_def.to_cartopy_crs()

eraland_analysis = xr.open_zarr("/ec/scratch/fab0/Projects/cerise/carra_snow_data/eraland.zarr")
eraland_dump = eraland_analysis.sel(time=date_selected)
eraland_dump = eraland_dump.isel(y=slice(None, None, -1)) #invert y axis

eraland_dump["bin_snow"] = (
   ["time","y", "x"],  # specify dimensions. NOTE: 1000 here because era land uses m and not kg/m3 like carra or cerise
    np.where(eraland_dump["rsn"] != 0, (1000*eraland_dump["sd"] / eraland_dump["rsn"] > 0.01).astype(int), np.nan)
   )


colors = ['#FFFFFF00', '#FF0000']  # First color is transparent, second is red
custom_cmap = plt.matplotlib.colors.ListedColormap(colors)


kwargs = dict(vmin=0, vmax=1.0, cmap=custom_cmap)
fig, ax = plt.subplots(figsize=(10, 8),subplot_kw=dict(projection=crs),sharex="all",sharey="all")
im = map_field(eraland_dump["bin_snow"][0,:,:],ax, **kwargs)
cb = fig.colorbar(
            im, ax=ax, orientation="vertical", label="Binary snow", aspect=40
        )

fig.suptitle(f"Binary snow from ERA land on {date_selected}")
#plt.show()
fig.savefig(f"eraland_{date_selected}.png")
