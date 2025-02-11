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

carra1_analysis = xr.open_zarr("/ec/scratch/fab0/Projects/cerise/carra_snow_data/carrasnow_v2.zarr")
date_range = carra1_analysis.sel(time=slice("2016-09-01","2016-09-30"))
carra1_dump = date_range.sel(time="2016-09-15")
carra1_dump = carra1_dump.isel(y=slice(None, None, -1)) #invert y axis

#carra1_dump["bin_snow"] = np.where(carra1_dump["rsn"] != 0, (carra1_dump["sd"] / carra1_dump["rsn"] > 0.01).astype(int), np.nan)

carra1_dump["bin_snow"] = (
   ["time","y", "x"],  # specify dimensions
    np.where(carra1_dump["rsn"] != 0, (carra1_dump["sd"] / carra1_dump["rsn"] > 0.01).astype(int), np.nan)
   )


colors = ['#FFFFFF00', '#FF0000']  # First color is transparent, second is red
custom_cmap = plt.matplotlib.colors.ListedColormap(colors)


kwargs = dict(vmin=0, vmax=1.0, cmap=custom_cmap)
fig, ax = plt.subplots(figsize=(10, 8),subplot_kw=dict(projection=crs),sharex="all",sharey="all")
im = map_field(carra1_dump["bin_snow"][0,:,:],ax, **kwargs)
cb = fig.colorbar(
            im, ax=ax, orientation="vertical", label="Binary snow", aspect=40
        )

fig.suptitle("Binary snow from CARRA1 East on 2016-09-15")
plt.show()
fig.savefig("carra1.png")
