import xarray as xr
import numpy as np

import cartopy.crs as ccrs
import pyproj
import pyresample
import datetime
import pandas as pd
import matplotlib.pyplot as plt


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

cerise_analysis = xr.open_zarr("/ec/scratch/fab0/Projects/cerise/carra_snow_data/ana_v2.zarr")
cerise_subset = cerise_analysis.mean(dim="member")
cerise_subset["bin_snow"]  = xr.where(cerise_subset["hxa"] > 0.01, 1, 0)  
date_range = cerise_subset.sel(time=slice("2016-09-01","2016-09-30"))
cerise_dump = date_range.sel(time="2016-09-01")
cerise_dump = cerise_dump.isel(y=slice(None, None, -1)) #not sure why I need to do it here and not in the others...

colors = ['#FFFFFF00', '#FF0000']  # First color is transparent, second is red
custom_cmap = plt.matplotlib.colors.ListedColormap(colors)


kwargs = dict(vmin=0, vmax=1.0, cmap=custom_cmap)
fig, ax = plt.subplots(figsize=(10, 8),subplot_kw=dict(projection=crs),sharex="all",sharey="all")
im = map_field(cerise_dump["bin_snow"][:,:,0],ax, **kwargs)
cb = fig.colorbar(
            im, ax=ax, orientation="vertical", label="Binary snow", aspect=40
        )

fig.suptitle("Binary snow from CERISE on 2016-09-01")
plt.show()
fig.savefig("cerise.png")
