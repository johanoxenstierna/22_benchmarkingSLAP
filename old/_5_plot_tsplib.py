"""
THIS PLOTS THE TSPLIB GENERATED IN _2_GENERATOR
AB is extended to include everything needed for plotting
"""

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import imread
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import pickle


def rotate_list(l, n):
	return l[n:] + l[:n]


fig = plt.figure(num=1, figsize=(10, 7))
ax = fig.subplots()
img = imread('./benchmarking/mapEmpty.png')  # used so warehouse can be added when desired
ax.imshow(img, extent=[0, 80, 0, 80], alpha=0.4)

with open('./benchmarking/BDEV_May_2020/AB', 'rb') as f:
	AB = pickle.load(f)

with open('./client-data/bench/optimizer-data/allcoords', 'rb') as f:
	allcoords = pickle.load(f)

with open('./benchmarking/BDEV_May_2020/tsplib_di_temp', 'rb') as f:
	di = pickle.load(f)

colors = ['seagreen', 'navy', 'red', 'lime', 'royalblue', 'maroon', 'crimson', 'firebrick',
				  'darkorange', 'darkolivegreen', 'steelblue', 'darkcyan',
				  'darkgoldenrod', 'darkcyan', 'purple', 'darkslategray']   #

ax.plot(40, 40, 'D', color='red', markersize=8.)  # depot

# AB extension loop
ii = 0
for box_id in AB:
	box = AB[box_id]
	box['box_x_coords'] = []
	box['box_y_coords'] = []
	for pl in box['pick_locs']:
		box['box_x_coords'].append(allcoords[int(pl)][0])
		box['box_y_coords'].append(allcoords[int(pl)][1])
	box['color'] = colors[0]
	colors = rotate_list(colors, 1)
	ii += 1


# OBSTACLES (does not use same dict as below) -------------------
try:  # can't use if since obstacles may not even be there
	num_polygons = len(di['OBSTACLES'])
	patches = []
	import numpy as np
	for key_obstacle in di['OBSTACLES']:
		inds = di['OBSTACLES'][key_obstacle]
		num_sides = len(inds)
		coords = []
		for ind in inds:
			x = int(di['LOCATION_COORD_SECTION'][ind][0])
			y = int(di['LOCATION_COORD_SECTION'][ind][1])
			coords.append([x, y])

		polygon = Polygon(coords, True)
		patches.append(polygon)
		bb = 5

	p = PatchCollection(patches, edgecolors='black', facecolors='none')
	ax.add_collection(p)
except:
	print("Except... plot_res -> OBSTACLES. May be what you want")

# plotter loop
for box_id in AB:
	box = AB[box_id]

	ax.plot(box['box_x_coords'], box['box_y_coords'], 'o', color=box['color'], markersize=5., linewidth=5)

	for i in range(len(box['pick_locs'])):
		x_coord = box['box_x_coords'][i]
		y_coord = box['box_y_coords'][i]

		ax.annotate(str(box['available_from']), xy=(x_coord, y_coord), fontsize=8, fontweight="bold", xytext=(x_coord - 1, y_coord + 1), color='black')

plt.show()