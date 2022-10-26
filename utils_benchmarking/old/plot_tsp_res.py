
import os
import json
import time
import pickle
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection


def rotate_list(l, n):
	return l[n:] + l[:n]


def plot_res_separated(specs, EXPORT_PATH_and_name, obstacles_all):
	"""
	PLOTS ALL SOLUTIONS SEPARATELY (USEFUL WITH DYNAMICITY)
	OBS REQUIRES ENUMERATED NAMING OF GENERATED JSONS
	di: tsplib dict
	# OBS NEW THE GUI-TEST FOLDER GETS REMOVED SEE BOTTOM
	:return:
	"""

	time0 = time.time()
	PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"
	_, folders, file_names = os.walk(PATH_gui_test).__next__()  # name, folders, file names
	num_jsons = len(file_names)
	print("time to name folders: " + str(time.time() - time0))

	time_test = 0
	time_test2 = 0

	for i in range(0, num_jsons + 1):

		time0 = time.time()

		if i == 0:  # this is cuz 0 is the special case of just showing coordinates
			k = 1  # this is only used since the created pics in gui-test start enumeration at 1
		else:
			k = i  # I.E. two pictures will be generated in first iteration. BUT a condition below makes sure first is without lines.

		PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"

		fig = plt.figure(num=1, figsize=(3, 3), dpi=100)  # 10, 7  dpi=80 results in c*f*k
		ax = fig.subplots()
		ax.set_xlim([0, 78])
		ax.set_ylim([0, 78])
		ax.set_xticks([0, 40, 80])
		ax.set_yticks([0, 40, 80])

		# # PLOT LOCATIONS (ALL) IF IT'S A STORAGE ASSIGNMENT CASE
		# if specs['requestType'] == 'STORAGE_ASSIGNMENT':
		# 	with open('./client-data/bench/Slotting/optimizer-data/allcoords', 'rb') as f:
		# 		allcoords = pickle.load(f)
		#
		# 	xs = [x[0] for x in allcoords]
		# 	ys = [x[1] for x in allcoords]
		#
		# 	ax.plot(xs, ys, 's', markersize=3, color='black')

		#OBSTACLES:
		patches = []
		for key, val in obstacles_all.items():
			coords = []
			for corner in val['corners']:
				x = corner[0]
				y = corner[1]

				coords.append([x, y])

			polygon = Polygon(coords, True)
			patches.append(polygon)

		p = PatchCollection(patches, edgecolors='black', facecolors='none')
		ax.add_collection(p)

		with open(PATH_gui_test + str(k) + ".json", 'r') as f:  # ONLY WORKS FOR ENUMERATED FIX
			optim = json.load(f)  # In python, the json is converted to a dictionary

		# PLOT LINES --------------
		x_optim = [int(float(i['x'])) for i in optim['webAppData']['pickRun']['fullPathCoords']]
		y_optim = [int(float(i['y'])) for i in optim['webAppData']['pickRun']['fullPathCoords']]

		if i > 0:  # ONLY USE LINES IF IT'S NOT THE 0 PIC
			ax.plot(x_optim, y_optim, color='black', linewidth=2,  # 0.
			        linestyle='-', alpha=1)  # plots sol

		# PLOT origin/destination ---------------------
		ax.plot(x_optim[0], y_optim[0], 'D', color='blue', markersize=8)  # 0.
		ax.plot(x_optim[-1], y_optim[-1], 'D', color='red', markersize=8)  # 0.

		colors = ['seagreen', 'red', 'lime', 'firebrick', 'lime',
		          'darkorange', 'darkolivegreen', 'maroon',
		          'darkgoldenrod', 'darkcyan', 'purple', 'darkslategray', 'crimson']

		time_test += time.time() - time0
		for box_id in optim['webAppData']['pickRun']['boxesNodeCoords']:  # this plots over nodes if such have already been plotted
			time1 = time.time()
			box = optim['webAppData']['pickRun']['boxesNodeCoords'][box_id]

			xs = [int(float(x[0])) for x in box['coords']]
			ys = [int(float(x[1])) for x in box['coords']]

			col = colors[int(box_id) % len(colors) - 1]  # -1 because box id's start on '1' whereas cols start on 0

			# col = colors[0]
			# colors = rotate_list(colors, 1)  # pending del

			if box['type'] == 'batched' and i != 0:
				ax.plot(xs, ys, 'o', color=col, markersize=6)  # 0.
			else:
				ax.plot(xs, ys, 'o', color=col, markersize=2)  # 0.

			time_test2 += time.time() - time1

		# plt.show()
		time0 = time.time()
		fig.savefig(EXPORT_PATH_and_name + '_' + str(i) + '.png')  # THIS IS THE ONE!!! @@@@***ITSHITSHITSH
		time_test += time.time() - time0

	print("time_test: " + str(time_test))
	print("time_test2: " + str(time_test2))

	time3 = time.time()
	# OBS NEW THE GUI-TEST FOLDER GETS REMOVED HERE
	warehouse_id = 'bench'
	import glob
	# folder_name_optim = "./gui-test/benchmark_data/BO_BQ_jsons/optim/*"
	folder_name_optim = "./gui-test/" + warehouse_id + "/BO_BQ_jsons/optim/*"
	files = glob.glob(folder_name_optim)
	for f in files:
		os.remove(f)
	print("time_test3: " + str(time.time() - time3))


def plot_res_combined(specs, EXPORT_PATH_and_name, obstacles_all):
	"""
		PLOTS ALL SOLUTIONS IN ONE SINGLE PICTURE
		OBS REQUIRES ENUMERATED NAMING OF GENERATED JSONS
		di: tsplib dict
		# OBS NEW THE GUI-TEST FOLDER GETS REMOVED SEE BOTTOM
		:return:
		"""

	time0 = time.time()
	PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"
	_, folders, file_names = os.walk(PATH_gui_test).__next__()  # name, folders, file names
	num_jsons = len(file_names)
	print("time to name folders: " + str(time.time() - time0))

	time_test = 0
	time_test2 = 0

	fig, (ax0, ax1) = plt.subplots(1, 2, sharex=True, sharey=True, figsize=(6, 3), dpi=100)
	ax0.set_xlim([0, 78])
	ax0.set_ylim([0, 78])
	ax0.set_xticks([0, 40, 80])
	ax1.set_xticks([0, 40, 80])  # 80 was missing for some reason
	ax0.set_yticks([0, 40, 80])

	# # PLOT LOCATIONS (ALL) IF IT'S A STORAGE ASSIGNMENT CASE
	#TODO: don't plot depot "1" if it's non-DARP
	if specs['requestType'] == 'STORAGE_ASSIGNMENT':
		with open('./client-data/bench/Slotting/optimizer-data/allcoords', 'rb') as f:
			allcoords = pickle.load(f)

		xs = [x[0] for x in allcoords]
		ys = [x[1] for x in allcoords]

		ax0.plot(xs, ys, 's', markersize=3, color='black')
		ax1.plot(xs, ys, 's', markersize=3, color='black')

	for i in range(0, num_jsons + 1):
	# for i in range(0, 2):

		time0 = time.time()

		if i == 0:  # this is cuz 0 is the special case of just showing coordinates
			k = 1  # this is only used since the created pics in gui-test start enumeration at 1
		else:
			k = i  # I.E. two pictures will be generated in first iteration. BUT a condition below makes sure first is without lines.

		PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"

		# OBSTACLES:
		patches = []
		for key, val in obstacles_all.items():
			coords = []
			for corner in val['corners']:
				x = corner[0]
				y = corner[1]

				coords.append([x, y])

			polygon = Polygon(coords, True)
			patches.append(polygon)

		p0 = PatchCollection(patches, edgecolors='black', facecolors='none')
		p1 = PatchCollection(patches, edgecolors='black', facecolors='none')
		ax0.add_collection(p0)
		ax1.add_collection(p1)

		with open(PATH_gui_test + str(k) + ".json", 'r') as f:  # ONLY WORKS FOR ENUMERATED FIX
			optim = json.load(f)  # In python, the json is converted to a dictionary

		# PLOT LINES --------------
		x_optim = [int(float(i['x'])) for i in optim['webAppData']['pickRun']['fullPathCoords']]
		y_optim = [int(float(i['y'])) for i in optim['webAppData']['pickRun']['fullPathCoords']]

		if i > 0:  # ONLY USE LINES IF IT'S NOT THE 0 PIC
			ax1.plot(x_optim, y_optim, color='black', linewidth=2,  # 0.
			        linestyle='-', alpha=1)  # plots sol

		# PLOT origin/destination ---------------------
		ax0.plot(x_optim[0], y_optim[0], 'D', color='blue', markersize=8)  # 0.
		ax0.plot(x_optim[-1], y_optim[-1], 'D', color='red', markersize=6)  # 0.
		ax1.plot(x_optim[0], y_optim[0], 'D', color='blue', markersize=8)  # 0.
		ax1.plot(x_optim[-1], y_optim[-1], 'D', color='red', markersize=6)  # 0.

		colors = ['seagreen', 'red', 'lime', 'firebrick', 'lime',
		          'darkorange', 'darkolivegreen', 'maroon',
		          'darkgoldenrod', 'darkcyan', 'purple', 'darkslategray', 'crimson']

		time_test += time.time() - time0
		for box_id in optim['webAppData']['pickRun'][
			'boxesNodeCoords']:  # this plots over nodes if such have already been plotted
			time1 = time.time()
			box = optim['webAppData']['pickRun']['boxesNodeCoords'][box_id]

			xs = [int(float(x[0])) for x in box['coords']]
			ys = [int(float(x[1])) for x in box['coords']]

			col = colors[int(box_id) % len(colors) - 1]  # -1 because box id's start on '1' whereas cols start on 0

			if box['type'] == 'batched' and i != 0:
				ax0.plot(xs, ys, 'o', color=col, markersize=6)  # 0.
				ax1.plot(xs, ys, 'o', color=col, markersize=6)  # 0.
			else:
				ax1.plot(xs, ys, 'o', color=col, markersize=1)  # 0.

			time_test2 += time.time() - time1

		# plt.show()
	time0 = time.time()
	fig.savefig(EXPORT_PATH_and_name + '.png')  # THIS IS THE ONE!!! @@@@***ITSHITSHITSH
	time_test += time.time() - time0

	print("time_test: " + str(time_test))
	print("time_test2: " + str(time_test2))

	time3 = time.time()
	# OBS NEW THE GUI-TEST FOLDER GETS REMOVED HERE
	warehouse_id = 'bench'
	import glob
	# folder_name_optim = "./gui-test/benchmark_data/BO_BQ_jsons/optim/*"
	folder_name_optim = "./gui-test/" + warehouse_id + "/BO_BQ_jsons/optim/*"
	files = glob.glob(folder_name_optim)
	for f in files:
		os.remove(f)
	print("time_test3: " + str(time.time() - time3))


# plt.imsave(fig, './tempte2.png', cmap='gray')

# if __name__ == '__main__':
# 	plot_res()