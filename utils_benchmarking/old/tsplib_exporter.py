import os
import json
import pickle
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

class TSPLIBexporter:
	"""
	Exporter class for benchmark tsplibs.
	"""
	def __init__(self, specs, EXPORT_PATH_OUTER,
				 x_optimization_times, di, OPTIMIZER_USED):  #, sol_jsons, di, tot_distance_m):
		"""

		:param specs:
		:param EXPORT_PATH_OUTER: This points to the warehouse type folder
		The "INNER" one points to the actual tsplib folder (based on the name of the instance).
		INNER_INNER is the optimizer folder
		:param result_distance:
		:param x_optimization_times:
		:param sol_jsons:
		"""
		self.s = specs
		self.flag_first_run = True
		if self.s['nameTsplib'] != None:
			self.flag_first_run = False

		# self.EXPORT_PATH_OUTER = EXPORT_PATH_OUTER
		# self.result_distance = result_distance
		self.x_optimization_times = x_optimization_times
		# self.sol_jsons = sol_jsons
		self.di = di  # the generator di
		# with open(self.s['path_local'] + 'meta/tsplib_di_temp.json', 'rb') as f:
		# 	self.di = json.load(f)  # abbreviated to save linespace!

		with open(self.s['path_local'] + 'meta/obstacles_all.json', 'r') as f:
			self.obstacles_all = json.load(f)

		self.EXPORT_PATH_INNER = EXPORT_PATH_OUTER + self.di['NAME'] + "/"
		self.EXPORT_PATH_INNER_INNER = self.EXPORT_PATH_INNER + OPTIMIZER_USED + "/"

		if self.flag_first_run == True:  # i.e. it hasn't been created yet
			os.mkdir(self.EXPORT_PATH_INNER)
		os.mkdir(self.EXPORT_PATH_INNER_INNER)

		self.BO_jsons = self.load_gui_test_jsons()
		self.sols_json, self.total_dist_m, self.total_comp_time = self.aggregate_json_result_data()

		# self.validate_sol_tsplib()

	def load_gui_test_jsons(self):
		BO_jsons = {}
		PATH = './gui-test/' + self.s['obstaclesType'] + '/BO_jsons/optim/'
		_, _, files = os.walk(PATH).__next__()
		for name in files:
			with open(PATH + name, 'r') as f:
				BO_jsons[name] = json.load(f)

		return BO_jsons

	def aggregate_json_result_data(self):

		total_dist_m = 0
		total_comp_time = 0
		sols_json = {}  # the json that is saved in tsplib folder
		ii = 1
		for _, val in self.BO_jsons.items():
			key_new = "batch_" + str(ii)
			res = val['responseData']
			dist = res['batchAsPickRoute']['totalDistanceMeters'] * 10
			time = res['responseTimeTakenSeconds']

			sol_entry = {'orders': res['ordersInBatch'],
						 'pickRoute': res['batchAsPickRoute']['locations'],
						 "SKUs": res['batchAsPickRoute']['SKUs'],
						 "distance": dist, "computational_time": time}
			sols_json[key_new] = sol_entry

			total_dist_m += dist
			total_comp_time += time
			ii += 1

		return sols_json, total_dist_m, total_comp_time

	def update_tsplib_header(self):
		old_res = float(self.di['HEADER']['COMMENTS']['Best known objective'])
		old_comptime = float(self.di['HEADER']['COMMENTS']['Computational time (s)'])
		new_res = float(self.di['HEADER']['COMMENTS']['Best known objective'])
		if old_res < new_res:
			self.di['HEADER']['COMMENTS']['Best known objective'] = str(old_res)
			self.di['HEADER']['COMMENTS']['Computational time (s)'] = str(old_comptime)

	def export_sol(self):

		with open(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '_sol.json', 'w') as f:
			json.dump(self.sols_json, f, indent=4)

	def export_tsplib_jsons(self):
		"""
		OBS A TSPLIB IS STORED
		Exports 1. tsplib as json (for easier use later), 2. tsplib as txt
		3. save self.sol_jsons
		Does not store results of individual QuickBatch calls (do separate investigation session)
		"""

		# TSPLIB JSON EXPORT --------------------------------------------
		self.di['HEADER']['COMMENTS']["Best known objective"] = str(round(self.total_dist_m, 3))  # converted to dm (should still be float)
		self.di['HEADER']['COMMENTS']["Computational time (s)"] = str(self.total_comp_time)  # converted to dm (should still be float)

		# if self.s['requestType'] != "storageAssignment":
		# 	LOCATION_COORD_SECTION = []

		# name = self.di['NAME']
		print("saving " + str(self.di['NAME']))
		# if self.flag_first_run == True:  # i.e. it hasn't been created yet
		# 	os.mkdir(self.EXPORT_PATH_INNER)
		# self.EXPORT_PATH_OUTER = self.EXPORT_PATH_OUTER + name + "/"

		# PATH_SOL = self.EXPORT_PATH_INNER + self.sol_jsons['optimizerUsed'] + "/"


		# SAVE TSPLIB JSON ====================
		# if self.s['requestType'] != 'storageAssignment':

		if self.flag_first_run == False:
			self.validate_update_jsons_OBP()

		# DELETE FIELDS WHICH ARE ALREADY THERE IN PARENT.
		del self.di['DEPOTS']
		del self.di['NUM_DEPOTS']
		del self.di['NUM_LOCATIONS']
		del self.di['depotSection']
		del self.di['OBSTACLES']
		del self.di['TYPE']

		time0 = time.time()
		with open(self.EXPORT_PATH_INNER + self.di['NAME'] + '.json', 'w') as f:  # with line breaks etc.
			json.dump(self.di, f, indent=4, sort_keys=True)  # indent=4

		# with open(self.EXPORT_PATH_INNER + self.di['NAME'] + '.json', 'w') as f:  # compressed
		# 	json.dump(self.di, f, sort_keys=True)

		# SAVE SOLUTION --------------------------------------

		# self.sol_jsons['solutionDistance'] = self.result_distance * 10
		# self.sol_jsons['computationalTime(s)'] = total_comp_time

		print("time to save self.di: " + str(time.time() - time0))

		# SAVE SPECS ===========================
		self.s['nameTsplib'] = self.di['NAME']
		with open(self.EXPORT_PATH_INNER + self.di['NAME'] + '_specs.json', 'w') as f:
			json.dump(self.s, f, indent=4)  # , sort_keys=True)

		time0 = time.time()
		print("time to save plot_res: " + str(time.time() - time0))
		print("\n")

	def export_tsplib_textfile(self):
		# TSPLIB TXT EXPORT -----------------------------------------
		li_h = []
		li_h.append(self.di['HEADER']['VERSION'])
		for key in self.di['HEADER']['COMMENTS']:  # assumes sorted
			comment = self.di['HEADER']['COMMENTS'][key]
			li_h.append("COMMENT: " + key + ": " + comment)

		li = ["NAME: " + self.di['NAME'],
		      # "NUM_DEPOTS: " + str(len(self.di['DEPOTS'])),
		      "NUM_CAPACITIES: " + str(self.di['NUM_CAPACITIES']),
		      "NUM_VISITS: " + str(self.di['NUM_VISITS']),
		      # "NUM_LOCATIONS: " + str(self.di['NUM_LOCATIONS']),  # only in parent
		      "NUM_VEHICLES: " + str(self.di['NUM_VEHICLES']),
		      "CAPACITIES: " + str(self.di['CAPACITIES']),
		      "DATA_SECTION"
		      ]

		li = li_h + li

		# needed variables
		# num_locations = len(self.di['LOCATION_COORD_SECTION'])
		# if self.s['requestType'] == 'storageAssignment':
		# 	num_locations = len(self.di['LOCATION_COORD_SECTION'])  # obs sometimes a lesser number is needed
		# else:
		# 	num_locations = len(self.di['VISIT_LOCATION_SECTION'])

		num_orders = len(self.di['ORDERS'])

		start_c = 1
		if len(self.s['depotSection']) == 1:
			li.append("DEPOTS\n  0")
		elif len(self.s['depotSection']) == 2:
			start_c = 2  # otherwise VISIT_LOCATION_SECTION will start at 1 which is not true for DARP
			li.append("DEPOTS\n  0\n  1")
		else:
			raise Exception("joEx number of depots can only be 1 or 2")

		# DEMAND_SECTION = ""
		VISIT_LOCATION_SECTION = ""
		when_to_terminate = int(list(self.di['VISIT_LOCATION_SECTION'].keys())[-1]) + 1  # ASSUMES IT'S SORTED

		for i in range(start_c, when_to_terminate):  # NUM_VISITS can't be used since start_c may start at > 1

			eol_char = '\n'
			if i == when_to_terminate - 1:
				eol_char = ''
			# DEMAND_SECTION += '  ' + str(i) + ' 1' + eol_char  # -1 is deliver, +1 is pickup  # only needed when capacities is for products
			VISIT_LOCATION_SECTION += '  ' + str(i) + ' ' + self.di['VISIT_LOCATION_SECTION'][str(i)] + eol_char

		# li.append("DEMAND_SECTION\n" + DEMAND_SECTION)

		## THIS SHOULD BE MOVED TO tsplib_parent
		# LOCATION_COORD_SECTION = ""
		# for i in range(0, num_locations):
		# 	eol_char = '\n'
		# 	if i == num_locations - 1:
		# 		eol_char = ''
		# 	x = self.di['LOCATION_COORD_SECTION'][str(i)][0]
		# 	y = self.di['LOCATION_COORD_SECTION'][str(i)][1]
		# 	LOCATION_COORD_SECTION += '  ' + str(i) + ' ' + x + ' ' + y + eol_char
		#
		# li.append("LOCATION_COORD_SECTION\n" + LOCATION_COORD_SECTION)
		# if self.di['NUM_DEPOTS'] == "1":
		# 	li.append("DEPOT_LOCATION_SECTION\n  0")
		# elif self.di['NUM_DEPOTS'] == "DARP":
		# 	li.append("DEPOT_LOCATION_SECTION\n  40 40\n  35 35")  # temp
		li.append("VISIT_LOCATION_SECTION\n" + VISIT_LOCATION_SECTION)
		li.append("COMMENT: TIMESTEP: 1")

		ORDERS = ""
		TIME_AVAIL_SECTION = ""  # OBS THIS WILL BE DIFFERENT IF ORDER-INTEGRITY NOT REQUIRED
		for i in range(1, num_orders + 1):  # assumes orders are numbered starting at 1
			eol_char = '\n'
			if i == num_orders:
				eol_char = ''

			TIME_AVAIL_SECTION += '  ' + str(i) + ' ' + self.di['TIME_AVAIL_SECTION'][str(i)] + eol_char

			# ORDER STRING
			box_items = self.di['ORDERS'][str(i)]
			items_str = ""
			for item_i in box_items:
				items_str += item_i + " "
			items_str = items_str[0:len(items_str) - 1]  # removes last empty space
			ORDERS += "  " + str(i) + " " + items_str + eol_char

		li.append("ORDERS_SECTION\n" + ORDERS)
		li.append("TIME_AVAIL_SECTION\n" + TIME_AVAIL_SECTION)

		# if len(self.di['OBSTACLES']) > 0:
		# 	OBSTACLES = ""
		# 	for i in range(1, len(self.di['OBSTACLES']) + 1):
		# 		eol_char = '\n'
		# 		if i == len(self.di['OBSTACLES']):
		# 			eol_char = ''
		#
		# 		obs_ind = self.di['OBSTACLES'][str(i)]
		# 		obs_str = ""
		# 		for ind in obs_ind:
		# 			obs_str += ind + " "
		# 		obs_str = obs_str[0:len(obs_str) - 1]
		# 		OBSTACLES += "  " + str(i) + " " + obs_str + eol_char
		#
		# 	li.append("OBSTACLES\n" + OBSTACLES)

		# if self.di['NUM_DEPOTS'] == "DARP":  # TEMP
		#     VEH_DEPOT_SECTION = ""
		#     for i in range(1, len(self.di['VEH_DEPOT_SECTION']) + 1):
		#         eol_char = '\n'
		#         if i == len(self.di['VEH_DEPOT_SECTION']):
		#             eol_char = ''
		#         aa = str(self.di['VEH_DEPOT_SECTION'][str(i)][0])
		#         VEH_DEPOT_SECTION += "  " + str(self.di['VEH_DEPOT_SECTION'][str(i)][0]) + " " + str(self.di['VEH_DEPOT_SECTION'][str(i)][1]) + eol_char
		#     li.append("VEH_DEPOT_SECTION\n" + VEH_DEPOT_SECTION)
		li.append("EOF")

		# SHOULD ALWAYS BE SAVED SINCE BEST FOUND RESULT IS UPDATED
		with open(self.EXPORT_PATH_INNER + self.di['NAME'], 'w') as f:
			for i in range(len(li)):
				f.write(li[i] + "\n")

	def validate_update_jsons_OBP(self):
		"""
		TOTALLY DEPRECATED. ONE TSPLIB TO RULE THEM ALL
		Checks old and new jsons values are same and updates best result in the new json.
		:return:
		"""

		# old_optimizer_used = None
		# if self.sol_jsons['optimizerUsed'] == 'COG':
		# 	old_optimizer_used = 'SMD'
		# elif self.sol_jsons['optimizerUsed'] == 'SMD':
		# 	old_optimizer_used = 'COG'

		_, folder_names, file_names = os.walk(self.EXPORT_PATH_INNER).__next__()
		with open(self.EXPORT_PATH_INNER + self.s['nameTsplib'] + '.json', 'r') as f:
			old_di = json.load(f)

		# moved to new function
		# old_res = float(old_di['HEADER']['COMMENTS']['Best known objective'])
		# old_comptime = float(old_di['HEADER']['COMMENTS']['Computational time (s)'])
		# new_res = float(self.di['HEADER']['COMMENTS']['Best known objective'])
		# if old_res < new_res:
		# 	self.di['HEADER']['COMMENTS']['Best known objective'] = str(old_res)
		# 	self.di['HEADER']['COMMENTS']['Computational time (s)'] = str(old_comptime)

		assert (old_di['NUM_VISITS'] == self.di['NUM_VISITS'])
		assert (old_di['NUM_LOCATIONS'] == self.di['NUM_LOCATIONS'])
		assert (len(old_di['LOCATION_COORD_SECTION']) == len(self.di['LOCATION_COORD_SECTION']))
		for i in range(0, len(old_di['LOCATION_COORD_SECTION'])):
			x_old = int(old_di['LOCATION_COORD_SECTION'][str(i)][0])
			y_old = int(old_di['LOCATION_COORD_SECTION'][str(i)][1])

			x_new = int(self.di['LOCATION_COORD_SECTION'][str(i)][0])
			y_new = int(self.di['LOCATION_COORD_SECTION'][str(i)][1])
			try:
				assert(x_old == x_new)
				assert(y_old == y_new)
			except:
				ff =5

		assert (old_di['ORDERS'] == self.di['ORDERS'])
		assert (old_di['DEPOTS'] == self.di['DEPOTS'])
		# assert (old_di['HEADER'] == self.di['HEADER'])  # since it may have been unupdated
		assert (old_di['DEPOTS'] == self.di['DEPOTS'])
		assert (old_di['NUM_DEPOTS'] == self.di['NUM_DEPOTS'])
		assert (old_di['NAME'] == self.di['NAME'])
		assert (old_di['NUM_CAPACITIES'] == self.di['NUM_CAPACITIES'])
		assert (old_di['NUM_VEHICLES'] == self.di['NUM_VEHICLES'])
		assert (old_di['CAPACITIES'] == self.di['CAPACITIES'])
		assert (old_di['VISIT_LOCATION_SECTION'] == self.di['VISIT_LOCATION_SECTION'])
		assert (old_di['TIME_AVAIL_SECTION'] == self.di['TIME_AVAIL_SECTION'])
		assert (old_di['OBSTACLES'] == self.di['OBSTACLES'])

	def validate_sol_tsplib(self):
		"""
		TODO: REPLACE sol_jsons WITH gui-test
		Checks that the sol_json entries are correct relative to tsplib.
		:return:
		"""

		for i, batch in enumerate(self.sol_jsons['solutionOBP'][1]):

			for sku in batch['SKUs']:

				flag_found_order = False
				for possible_order in batch['orders']:
					po_in_di = self.di['ORDERS'][possible_order]
					if sku in po_in_di:
						flag_found_order = True
						break

				if flag_found_order == False:
					raise Exception("joEx something is wrong with solution json")

	def plot_res_separated(self):
		"""
		PLOTS ALL SOLUTIONS SEPARATELY (USEFUL WITH DYNAMICITY)
		OBS REQUIRES ENUMERATED NAMING OF GENERATED JSONS
		self.di: tsplib dict
		# OBS NEW THE GUI-TEST FOLDER GETS REMOVED SEE BOTTOM
		:return:
		"""

		time0 = time.time()
		PATH_gui_test = "./gui-test/" + self.s['obstaclesType'] + "/BO_jsons/optim/"
		_, folders, file_names = os.walk(PATH_gui_test).__next__()  # name, folders, file names
		if len(self.sols_json) != len(file_names):
			raise Exception("joEx gui-test jsons not same as number of solution batches. Try restart main (assuming it deltes old folders)")
		print("time to name folders: " + str(time.time() - time0))

		time_test0_save_figs = 0
		time_test2 = 0
		num_pics_saved = 0  # for debug
		file_names.insert(1, file_names[0])  # dummy inserted at beginning to plot map

		for i in range(0, len(file_names)):

			time0 = time.time()

			# if i == 0:  # this is cuz 0 is the special case of just showing coordinates
			# 	k = 1  # this is only used since the created pics in gui-test start enumeration at 1
			# else:
			# 	k = i  # I.E. two pictures will be generated in first iteration. BUT a condition below makes sure first is without lines.

			PATH_gui_test = "./gui-test/" + self.s['obstaclesType'] + "/BO_jsons/optim/"

			fig = plt.figure(num=1, figsize=(3, 3), dpi=100)  # 10, 7  dpi=80 results in c*f*k
			ax = fig.subplots()
			ax.set_xlim([0, 78])
			ax.set_ylim([0, 78])
			ax.set_xticks([0, 40, 80])
			ax.set_yticks([0, 40, 80])

			# # PLOT LOCATIONS (ALL) IF IT'S A STORAGE ASSIGNMENT CASE
			if self.s['requestType'] == 'storageassignment':
				with open('./client-data/bench/Slotting/optimizer-data/allcoords', 'rb') as f:
					allcoords = pickle.load(f)
				xs = []
				ys = []
				for coords in allcoords:
					for _, obstacle in self.obstacles_all.items():
						if coords not in obstacle['corners']:
							xs.append(coords[0])
							ys.append(coords[1])
				# xs = [x[0] for x in allcoords]
				# ys = [x[1] for x in allcoords]
				ax.plot(xs, ys, 'o', markersize=3, color='black')

			# OBSTACLES:
			patches = []
			for key, val in self.obstacles_all.items():
				coords = []
				for corner in val['corners']:
					x = corner[0]
					y = corner[1]

					coords.append([x, y])

				polygon = Polygon(coords, True)
				patches.append(polygon)

			p = PatchCollection(patches, edgecolors='black', facecolors='none')
			ax.add_collection(p)

			with open(PATH_gui_test + file_names[i], 'r') as f:  # ONLY WORKS FOR ENUMERATED FIX
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

			time_test0_save_figs += time.time() - time0
			for box_id in optim['webAppData']['pickRun'][
				'boxesNodeCoords']:  # this plots over nodes if such have already been plotted
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
					ax.plot(xs, ys, 'o', color=col, markersize=3)  # 0.

				time_test2 += time.time() - time1

			# plt.show()
			time0 = time.time()
			fig.savefig(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '_' + str(i) + '.png')  # THIS IS THE ONE!!! @@@@***ITSHITSHITSH
			time_test0_save_figs += time.time() - time0
			num_pics_saved += 1
			plt.close()

		if num_pics_saved - 1 != len(self.sols_json):  # +1 for the instance pic
			raise Exception("joEx gui-test jsons not same as number of solution batches. Try restart main (assuming it deltes old folders)")
		print("time_test0_save_figs: " + str(time_test0_save_figs))
		print("time_test2: " + str(time_test2))

		time3 = time.time()
		# OBS NEW THE GUI-TEST FOLDER GETS REMOVED HERE
		warehouse_id = 'bench'
		import glob
		# folder_name_optim = "./gui-test/benchmark_data/BO_BQ_jsons/optim/*"
		folder_name_optim = "./gui-test/" + warehouse_id + "/BO_jsons/optim/*"
		files = glob.glob(folder_name_optim)
		for f in files:
			os.remove(f)
		print("time_test3: " + str(time.time() - time3))

	def plot_res_combined(self):
		"""
		PLOTS ALL SOLUTIONS IN ONE SINGLE PICTURE
		OBS REQUIRES ENUMERATED NAMING OF GENERATED JSONS
		self.di: tsplib dict
		# OBS NEW THE GUI-TEST FOLDER GETS REMOVED SEE BOTTOM
		:return:
		"""

		time0 = time.time()
		PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"
		_, folders, file_names = os.walk(PATH_gui_test).__next__()  # name, folders, file names
		file_names.insert(1, file_names[0])  # dummy inserted at beginning to plot map
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
		# TODO: don't plot depot "1" if it's non-DARP
		if self.s['requestType'] == 'storageassignment':
			with open('./client-data/bench/Slotting/optimizer-data/allcoords', 'rb') as f:
				allcoords = pickle.load(f)

			xs = [x[0] for x in allcoords]
			ys = [x[1] for x in allcoords]

			ax0.plot(xs, ys, 's', markersize=3, color='black')
			ax1.plot(xs, ys, 's', markersize=3, color='black')

		for i in range(0, len(file_names)):
			# for i in range(0, 2):

			time0 = time.time()

			# if i == 0:  # this is cuz 0 is the special case of just showing coordinates
			# 	k = 1  # this is only used since the created pics in gui-test start enumeration at 1
			# else:
			# 	k = i  # I.E. two pictures will be generated in first iteration. BUT a condition below makes sure first is without lines.

			PATH_gui_test = "./gui-test/bench/BO_jsons/optim/"

			# OBSTACLES:
			patches = []
			for key, val in self.obstacles_all.items():
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

			with open(PATH_gui_test + file_names[i], 'r') as f:  # ONLY WORKS FOR ENUMERATED FIX
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
		fig.savefig(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '.png')  # THIS IS THE ONE!!! @@@@***ITSHITSHITSH
		plt.close()
		time_test += time.time() - time0

		print("time_test: " + str(time_test))
		print("time_test2: " + str(time_test2))

		time3 = time.time()
		# OBS NEW THE GUI-TEST FOLDER GETS REMOVED HERE
		warehouse_id = 'bench'
		import glob
		# folder_name_optim = "./gui-test/benchmark_data/BO_BQ_jsons/optim/*"
		folder_name_optim = "./gui-test/" + warehouse_id + "/BO_jsons/optim/*"
		files = glob.glob(folder_name_optim)
		for f in files:
			os.remove(f)
		print("time_test3: " + str(time.time() - time3))