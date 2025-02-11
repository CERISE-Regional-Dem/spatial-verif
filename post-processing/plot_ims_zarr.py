import xarray as xr
import numpy as np
import pyproj
import pyresample
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

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

area_def = get_ana_areadef()
crs = area_def.to_cartopy_crs()

ims = xr.open_zarr("/scratch/fab0/Projects/cerise/carra_snow_data/ims.zarr")
ims["bin_snow"]  = xr.where(ims["IMS_Surface_Values"] == 4, 1, 0)  

date_range = ims.sel(time=slice("2016-09-01","2016-09-30"))

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


ims_dump = date_range.sel(time="2016-09-01") 
ims_dump = ims_dump.isel(y=slice(None, None, -1)) #not sure why I need to do it here and not in the others...
colors = ['#FFFFFF00', '#FF0000']  # First color is transparent, second is red
custom_cmap = plt.matplotlib.colors.ListedColormap(colors)
kwargs = dict(vmin=0, vmax=1.0, cmap=custom_cmap)


fig, ax = plt.subplots(figsize=(10, 8),subplot_kw=dict(projection=crs),sharex="all",sharey="all")
im = map_field(ims_dump["bin_snow"][0,:,:],ax, **kwargs)
cb = fig.colorbar(
            im, ax=ax, orientation="vertical", label="Binary snow", aspect=40
        )

fig.suptitle("Binary snow from IMS on 2016-09-01")
plt.show()
fig.savefig("ims.png")
