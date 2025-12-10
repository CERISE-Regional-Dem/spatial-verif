import xarray as xr
import numpy as np
from shapely.geometry import Point, Polygon
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as PlotPolygon
import sys

class PolygonSelector:
    def __init__(self, ax, ds, var_name):
        self.ax = ax
        self.ds = ds
        self.var_name = var_name
        self.coords = []
        self.poly = None
        self.line, = ax.plot([], [], 'r.-')

        # Connect event handlers
        self.cid_click = plt.connect('button_press_event', self.on_click)
        self.cid_key = plt.connect('key_press_event', self.on_key)

        print("Instructions:")
        print("- Left click to add polygon vertices")
        print("- Press 'Enter' to complete the polygon and print coordinates")
        print("- Press 'escape' to clear and start over")

    def on_click(self, event):
        if event.inaxes != self.ax:
            return

        self.coords.append((event.xdata, event.ydata))
        x, y = zip(*self.coords) if self.coords else ([], [])
        self.line.set_data(x, y)
        plt.draw()

    def on_key(self, event):
        if event.key == 'enter':
            if len(self.coords) >= 3:
                self.complete_polygon()
            else:
                print("Need at least 3 points to create a polygon!")
        elif event.key == 'escape':
            self.clear_polygon()

    def complete_polygon(self):
        if self.poly is not None:
            self.poly.remove()

        # Create and display the final polygon
        self.poly = PlotPolygon(self.coords, facecolor='red', alpha=0.3)
        self.ax.add_patch(self.poly)

        # Print the coordinates
        #print("\nPolygon Coordinates (lon, lat):")
        print("\nPolygon Coordinates (lat,lon):")
        for x, y in self.coords:
            print(f"{y:.6f} {x:.6f}")
            ###print(f"{x:.6f} {y:.6f}")
        ##print("\nPolygon Coordinates (lat,lon):")
        #for y,x in self.coords:
        #    print(f"{y:.6f} {x:.6f}")
        # Add first point again to close the polygon
        ##print(f"{self.coords[0][0]:.6f}, {self.coords[0][1]:.6f}")
        print(f"{self.coords[0][1]:.6f} {self.coords[0][0]:.6f}")

        plt.disconnect(self.cid_click)
        plt.disconnect(self.cid_key)
        plt.draw()

    def clear_polygon(self):
        self.coords = []
        self.line.set_data([], [])
        if self.poly is not None:
            self.poly.remove()
            self.poly = None
        plt.draw()

def select_polygon_from_netcdf(netcdf_file):
    # Read the NetCDF file
    ds = xr.open_dataset(netcdf_file)

    # Print available variables in the dataset
    print("Available variables in the dataset:", list(ds.data_vars))

    # Let user select a variable to plot
    var_name = list(ds.data_vars)[0]  # Default to first variable
    print(f"Using variable: {var_name}")

    # Create the initial plot
    fig, ax = plt.subplots(figsize=(10, 8))

    # Plot the variable using pcolormesh
    var_data = ds[var_name].values
    lon_data = ds.lon.values
    lat_data = ds.lat.values

    # Create the plot
    plt.pcolormesh(lon_data, lat_data, var_data)
    plt.colorbar(label=var_name)
    ax.set_title('Click to select polygon vertices')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')

    # Initialize the selector
    selector = PolygonSelector(ax, ds, var_name)
    plt.show()

# Usage example:
# select_polygon_from_netcdf('your_netcdf_file.nc')
#nc_file = sys.argv[1]
# select_polygon_from_netcdf('your_netcdf_file.nc')
select_polygon_from_netcdf("/media/cap/extra_work/CERISE/MET_CARRA1_vs_IMS_winter_2015/grid_stat_000000L_20151101_060000V_pairs.nc")
#select_polygon_from_netcdf("/media/cap/extra_work/CERISE/MET_CERISE_vs_IMS_paper/grid_stat_000000L_20160330_060000V_pairs.nc")
select_polygon_from_netcdf(nc_file)

