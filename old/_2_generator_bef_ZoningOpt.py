'''
Does everything. _4_ and _3_ do things individually.
allcoords and all other client data EXCEPT locKeyInd are read-only once created in the digitization
'''

import os
import glob
import pickle
import json
import random
import math
import numpy as np
import uuid
from copy import deepcopy
import benchmarking.utils_benchmarking.graph_gen_w_obstacles as _2_og
from benchmarking.utils_benchmarking import repr_tsplib

# the "bodict" is a JSON version of tsplib. obstacles added in function below (optional)
bodict_skeleton = {
	'TYPE': 'OBP',
	'NUM_VISITS': '',
	'NUM_LOCATIONS': '',
	'LOCATION_COORD_SECTION': [],
	'ORDERS': {},
	'DEPOTS': '',
	'NUM_DEPOTS': None,
}


class Generator:
	"""
	Creates AB (the dict used in the OBP loop) and bodict (bodict contains everything needed)
	Requires a obstacle_gen placeholder even if obstacles aren't there.
	"""

	def __init__(self, specs, EXPORT_PATH_OUTER, digit_type=None, just_visualize=False):  # , random_seed=None):
		"""

		:param specs:
		digit_warehouse: WAREHOUSE ONLY DIGITIZED ONCE. But it creates bo as well (though not necessary first time)
		:param just_visualize: Does not save any files only visualizes instance
		:param random_seed: random seed from previous instance used to reproduce tsplib
		"""

		self.bo = deepcopy(bodict_skeleton)
		self.slots = {}

		random.seed(specs['randomSeed'])

		self.s = specs
		self.bo['depotSection'] = self.s['depotSection']
		self.EXPORT_PATH_OUTER = EXPORT_PATH_OUTER

		self.s['numVehicles'] = self.s['numOrders'] // self.s['mobileUnitCapacities']['numOrders'] + 1


		if self.s['requestType'] == 'storageAssignment':
			self.CLIENT_DATA_PATH = "./client-data/bench/Slotting/optimizer-data/"
			self.folder_BDEV = './benchmarking/BDEV_files/bench/Slotting/'
		else:
			self.CLIENT_DATA_PATH = "./client-data/bench/" + self.s['obstaclesType'] + "/optimizer-data/"
			self.folder_BDEV = specs['folder_BDEV']

		if digit_type == 'digitize_warehouse':
			self.obstacles_gen_and_export()
			self.depots()
			# self.coordinates()
			self.gen_allcoords()

			if just_visualize is False:
				self.bow_and_client_data_export()
			else:
				self.visualize_coords()

		elif digit_type == 'digitize_AB':

			self.load_data()  # previously digitized data LOADED FROM BDEV
			self.boxes_location_placeholders()
			self.boxes_extra_modding()
			self.duplicate_visits()
			self.bodict_to_AB_converter()
			self.AB_to_AB_list_converter()

			self.flag_slotting_coords_success = False
			while self.flag_slotting_coords_success is False:
				self.coordinates_AB()
			self.locKeyInd_gen()
			self.get_locations_used()
			if self.s['requestType'] == "storageAssignment":
				self.add_locations_not_used_currently()
			self.add_obstacles()
			self.test_all_locations_then_export_locKeyInd()
			self.export_AB()
			self.tsplib_name()
			self.export_AB_tsplib_dict()


	def tsplib_name(self):
		if self.s['nameTsplib'] == None:
			self._tsplib_name = "c" + str(self.bo['NUM_VISITS']) + "_" + str(uuid.UUID(int=self.s['randomSeed']))[-4:]
			# _, folder_names, file = os.walk(self.EXPORT_PATH_OUTER).__next__()
			# if self._tsplib_name in folder_names:
			# 	raise Exception("joEx the tsplib name already exists!")
		else:
			self._tsplib_name = self.s['nameTsplib']

	def obstacles_gen_and_export(self):
		# self.bo['OBSTACLES'] = {[]}

		self._obs_gen = _2_og.GraphGenWithObstacles(self.s)
		self._obs_gen.define_obstacles(self.s['obstaclesType'], self.s['possibleVisitLocs'])
		self._obs_gen.gen_OBSTACLESANDDUMMYOBSTACLES()

		self.bo['num_pick_locs_warehouse'] = len(self._obs_gen.allowed_coords)  # should not include corners

		with open(self.folder_BDEV + 'obstacles_all', 'wb') as f:
			pickle.dump(self._obs_gen.obstacles_all, f)

	def depots(self):
		"""Move this to after obstacles have been generated"""

		# # OBS THIS IS HARDCODED (COULD PERHAPS LIVE IN SCHEMA BUT NOT OBVIOUS - DUE TO SCHEMA GETING TOO COMPLEX)
		# default_loc = (40, 40)  # (40, 40)
		# default_loc2 = (38, 30)

		# default_loc = (37, 5)  # (40, 40)
		# default_loc2 = (45, 5)

		# non_default_locs = [(40, 5), (5, 5), (75, 5), (75, 75)]
		# non_default_sel = random.choice(non_default_locs)
		# self.bo["DEPOT_LOCATION_SECTION"] = {"0": str(default_loc)}
		# self.bo["DEPOT_LOCATION_SECTION"] = self.s['DEPOT_LOCATION_SECTION']

		if len(self.s['depotSection']) == 1:
			self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['0'])
			self.bo['DEPOTS'] = ['0']  # only inds are shown
			self._obs_gen.allcoords = [self.s['depotSection']['0']]
			# self.bo["DEPOT_LOCATION_SECTION"] = {'0': '0'}

			aa =5
		# elif self.s['DEPOTS'] == "default_1":  # DEPR?
		# 	# while good_candidate ...
		# 	self.bo['LOCATION_COORD_SECTION'].append(default_loc)  # TODO randint
		# 	self.bo['DEPOTS'] = ['0']
		elif len(self.s['depotSection']) == 2:
			# while good_candidate ...
			self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['0'])
			self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['1'])
			self._obs_gen.allcoords = [self.s['depotSection']['0'], self.s['depotSection']['1']]  # new
			self.bo['DEPOTS'] = ['0', '1']
			self.bo['VEH_DEPOT_SECTION'] = {'1': [0, 1]}  # vehicle id: vehicle origin; that it does not have to end there (i.e. it has to end at 0)
			# self.bo["DEPOT_LOCATION_SECTION"] = {'0': '0', '1': '1'}

	def load_data(self):
			"""
			USE TO LOAD EXISTING DATA (even reproduces the UUID)
			CANNOT USE TSPLIB'S SINCE THAT WOULD REQUIRE RE-DIGITIZATION OF WHOLE WAREHOUSE FOR EVERY INSTANCE
			bo_warehouse only contains the necessary information about depots currently.
			:return:
			"""
			#  ============================


			# with open(folder_BDEV + 'AB_all', "rb") as f:
			# 	self.AB_all = pickle.load(f)
			#
			# with open('./benchmarking/bench_res', "rb") as f:
			# 	self.bench_res = pickle.load(f)

			with open(self.folder_BDEV + 'bo_warehouse', "rb") as f:
				self.bow = pickle.load(f)

			# TEST DEPOTS
			#
			# if self.bow['depotSection'] != self.s['depotSection']:   # this is inited (again) in OBP_simulator
			# 	raise Exception("joExc NUM DEPOTS IS HARDCODED when the warehouse is generated. "
			# 	                "Check the specs in OBP_simulator, needs to correspond. This is to verify that you"
			# 	                "are diligent when running OBP_simulator")

			# # TEST OBSTACLES TYPE
			# if self.bow['obstaclesType'] != self.s['obstaclesType']:   # this is inited (again) in OBP_simulator
			# 	raise Exception("joExc NUM DEPOTS IS HARDCODED when the warehouse is generated. "
			# 	                "Check the specs in OBP_simulator, needs to correspond. This is to verify that you"
			# 	                "are diligent when running OBP_simulator")

			self.bo['LOCATION_COORD_SECTION'] = deepcopy(self.bow['LOCATION_COORD_SECTION'])  # adds depot info
			self.bo['DEPOTS'] = self.bow['DEPOTS']

			with open(self.folder_BDEV + 'obstacles_all', "rb") as f:
				self.obstacles_all = pickle.load(f)

			bench_type = self.s['obstaclesType']
			if self.s['requestType'] == "storageAssignment":
				bench_type = 'bench'

			# LOAD DATA FROM DIGITAL TWIN =================
			# self.CLIENT_DATA_PATH = "./client-data/" + bench_type + "/Slotting/optimizer-data/"
			with open(self.CLIENT_DATA_PATH + 'allcoords', "rb") as f:
				self.allcoords = pickle.load(f)
			aa = 5
			# with open(self.CLIENT_DATA_PATH + 'locKeyInd', "rb") as f:  # NEEDED FOR SLOTTING
			# 	self.locKeyInd = pickle.load(f)

	def boxes_location_placeholders(self):
		"""
		Assigns item placeholders to boxes and counts number of items
		:return:
		"""
		item_i = 1
		start_c = 1
		if len(self.s['depotSection']) == 2:
			item_i = 2  # when there are two depots
			start_c = 2
		for i in range(1, self.s['numOrders'] + 1):
			# num_items_in_box = 60  # random.randint(self.s['itemsPerBoxLow'], self.s['itemsPerBoxHigh'])
			num_items_in_box = random.randint(self.s['itemsPerBoxLow'], self.s['itemsPerBoxHigh'])

			rr = range(item_i, item_i + num_items_in_box)
			self.bo['ORDERS'][str(i)] = {'items': [str(x) for x in rr]}

			item_i += len(rr)

		if self.s['requestType'] != "storageAssignment":
			self.bo['NUM_LOCATIONS'] = item_i + len(self.obstacles_all) * 4 # same number as order-pick locs + corners
		else:  # all locations + corners
			self.bo['NUM_LOCATIONS'] = self.bow['num_pick_locs_warehouse'] + len(self.obstacles_all) * 4 # march 30 2021

		self.bo['NUM_VISITS'] = item_i - 1  # single depot
		if len(self.s['depotSection']) == 2:
			self.bo['NUM_VISITS'] = item_i - 2
		self.num_visits_no_duplicates = deepcopy(self.bo['NUM_VISITS'])
		print("total number of items: " + str(item_i))

	def boxes_extra_modding(self):
		"""
		VERY CRUDE CURRENTLY FOR SLAP. PROBABLY SPLITS ORDERS 50-50 BETWEEN 2 TIME-STEPS
		:return:
		"""
		time_chunks = np.array_split(range(1, self.s['numOrders'] + 1), self.s['dynamicity']['numTimeSteps'])  # UBE
		_boxes_available_from = [list(x) for x in time_chunks]  # denumpy
		_boxes_available_from.insert(0, [0])  # MAYBE NOT. NEEDED TO PROVIDE STARTING POINT FOR ITERATION BELOW

		if self.s['numItemsToMove'] > 0:  # like duplicate items but more shufflish
			time_step_from = random.randint(1, max(1, self.s['dynamicity']['numTimeSteps'] - 1))  # max for single slotting zone case
			time_step_to = max(1, time_step_from - 1)  # to prevent slots from being broken too much
			num_items_to_move = 2  # random.randint(1, _boxes_available_from[time_step_from] - 1)
			items_to_move = random.sample(_boxes_available_from[time_step_from], num_items_to_move)
			for item in items_to_move:  # seems ok with single timestep
				_boxes_available_from[time_step_to].append(item)
				_boxes_available_from[time_step_from].remove(item)  # only removes 1 at a time

		for t in range(1, len(_boxes_available_from)):  # t = timestep
			orders_at_t = _boxes_available_from[t]
			for id in orders_at_t:
				self.bo['ORDERS'][str(id)]['available_from'] = t

	def duplicate_visits(self):
		"""
		Generates extra 'duplicate' locations inside same order or in different orders
		based on percentage
		:return:
		"""

		self.duplicate_items = {}
		if self.s['percDuplicates'] == 0:
			return  # early exit if there are no duplicates

		num_dupl = math.ceil(self.bo['NUM_VISITS'] * self.s['percDuplicates'] / 100)  # at least 1 duplicate if there is a per
		for i in range(num_dupl):
			from_key = random.choice(list(self.bo['ORDERS'].keys()))
			item = random.choice(self.bo['ORDERS'][from_key]['items'])
			to_key = random.choice(list(self.bo['ORDERS'].keys()))
			self.bo['ORDERS'][to_key]['items'].append(item)
			self.bo['NUM_VISITS'] += 1  # SINCE IT MAY BE DIFFERENT VEHICLES THAT VISIT THE COORDINATE
			self.duplicate_items[item] = {"coords": None}
		aa = 5

	def coordinates_AB(self):

		"""
		NEWER
		OBS!!! len(pl_kd) > 100:  check that line it allows duplicates even if such are not sought!
		kd = keydict
		TODO: ADD MORE TESTS TO CHECK THAT THE FIRST OBSTACLE CORODINATE STARTS AFTER THE LAST VISIT COORDINATE ETC
		:return:
		"""

		box_slots = np.array_split(range(1, self.s['numOrders'] + 1), self.s['numSlottingZones'])  # UBE
		box_slots = [list(x) for x in box_slots]  # denumpy

		used_kd = []  # this is only used in this function. Just stores the indicies taken by duplicates and other kd items

		# MANUAL COORDS FOR DUPLICATE ITEMS (USED IN BELOW LOOP) ==========================
		for duplicate_item_key in self.duplicate_items:
			ind_in_kd = str(random.randint(len(self.bow['depotSection']) + 1, self.bow['num_pick_locs_warehouse']))
			self.duplicate_items[duplicate_item_key]['coords'] = self.allcoords[int(ind_in_kd)]  # TEMP
			self.duplicate_items[duplicate_item_key]['ind_kd'] = ind_in_kd
			used_kd.append(ind_in_kd)

		# SLOTTING ZONES ===================================================
		slots = {}  # the slots are created using random mid-points
		if self.s['numSlottingZones'] < 2:
			slots['0'] = {'xrange': (2, 78), 'yrange': (2, 78), 'mid_point': (40, 40)}
		else:
			for i in range(0, self.s['numSlottingZones']):
				mid_point = [random.randint(20, 60), random.randint(20, 60)]
				# TODO: use while loop instead and only create additional slots when their midpoint is not too near
				# TODO: actually, this IS component that will be replaced by the first stage of the slotting algorithm
				# x_range = [max(0, mid_point[0] - random.randint(5, 40)), min(78, mid_point[0] + random.randint(5, 40))]
				# y_range = [max(0, mid_point[1] - random.randint(5, 40)), min(78, mid_point[1] + random.randint(5, 40))]

				x_range = [max(0, mid_point[0] - random.randint(30, 40)),
				           min(78, mid_point[0] + random.randint(30, 40))]  # 3CA case
				y_range = [max(0, mid_point[1] - random.randint(30, 40)),
				           min(78, mid_point[1] + random.randint(30, 40))]

				slots[str(i)] = {'xrange': x_range, 'yrange': y_range, 'mid_point': mid_point}

		# CREATE COORDS ==================================================
		LOCATIONS_USED = []

		largest_item_i = 0
		for box_key, box in self.AB.items():
			# box['pick_locs_in_keydict'] = box['pick_locs']
			box['pick_locs_in_keydict'] = []
			box_slot = None  # the slot which the b
			for i in range(0, len(box_slots)):
				if int(box_key) in box_slots[i]:
					box_slot = str(i)  # the box is assigned a slot key here (i.e. where it should be placed)

			for pl_ind in box['pick_locs']: # THIS GIVES COORDS TO PICK ITEMS

				if pl_ind in self.duplicate_items:  # NO SLOTTING FOR DUPL ITEMS (to avoid bugs)
					box['pick_locs_in_keydict'].append(self.duplicate_items[pl_ind]['ind_kd'])
					if self.allcoords[int(self.duplicate_items[pl_ind]['ind_kd'])] not in LOCATIONS_USED:  # IF LOCATION has not been used, add it. Else, it has been used
						LOCATIONS_USED.append(self.duplicate_items[pl_ind]['coords'])
				else:
					closest_slot = None
					attempts = 0
					while closest_slot != box_slot:
						ind_kd = str(random.randint(2, self.bow['num_pick_locs_warehouse'] - 1)) # kd=locKeyInd

						# 1. check that ind_kd is not already taken as a duplicate (temp?)
						if ind_kd in used_kd:  #  and len(ind_kd) < 100:
							continue   # if there are few locs left, then proceed to create coord even so

						# 2.
						coord_kd = self.allcoords[int(ind_kd)]  # OBS this does noclosest_slott mean that the coordinate can not be used in more than one order (CHECK THAT THIS IS TRUE)
						min_dist = self.s['min_dist_to_slotting_zone']
						closest_slot_temp = None
						for slot_key, slot in slots.items():
							slot_mid_point = slot['mid_point']
							dist_kd_to_slot = abs(coord_kd[0] - slot_mid_point[0]) + abs(coord_kd[1] - slot_mid_point[1])
							if dist_kd_to_slot < min_dist:
								min_dist = dist_kd_to_slot
								closest_slot_temp = slot_key
						if closest_slot_temp == box_slot and min_dist < self.s['min_dist_to_slotting_zone']:
							closest_slot = closest_slot_temp

						if attempts > 1000:
							# raise Exception("joEx slotting zones messed up")
							box['pick_locs_in_keydict'] = []  # hmmm
							print("Attempted slotting failure")
							return  # this function is called until the flag below is set
						attempts += 1

					used_kd.append(ind_kd)
					box['pick_locs_in_keydict'].append(ind_kd)
					if self.allcoords[int(ind_kd)] not in LOCATIONS_USED:
						LOCATIONS_USED.append(self.allcoords[int(ind_kd)])  # THIS IS THE WAREHOUSE INDS

		# aa = np.unique(LOCATIONS_NEW)  # pending del
		print("attempts needed to create coords within slotting zones: " + str(attempts))
		# if self.s['requestType'] != "storageAssignment":
		self.bo['LOCATION_COORD_SECTION'] = self.bo['LOCATION_COORD_SECTION'] + LOCATIONS_USED

		self.flag_slotting_coords_success = True

	def locKeyInd_gen(self):
		"""
		HAVE TO OVERWRITE client-data LOCKEYIND HERE!!!!!!! AND PERMUTATE ALL LOCATIONS EVERYWHERE !
		AB -> 'pick_locs_in_keydict' BECOME 'pick_locs'
		:return:
		"""

		# 0: INIT locKeyInd
		self.locKeyInd = {}
		for i in range(len(self.bo['depotSection'])):
			self.locKeyInd[str(i)] = i

		#1 PERMUATE LOCKEYIND
		for order_id, order in self.AB.items():
			for i in range(len(order['pick_locs'])):
				pick_loc = order['pick_locs'][i]
				pick_loc_in_keydict = order['pick_locs_in_keydict'][i]

				self.locKeyInd[pick_loc] = int(pick_loc_in_keydict)
				order['pick_locs_in_keydict'][i] = pick_loc

		aa = 5

	def get_locations_used(self):

		last_locKey_currently = len(self.locKeyInd)
		assert (last_locKey_currently == max([int(x) for x in self.locKeyInd]) + 1)  # check above. UBE
		assert (last_locKey_currently == len(self.bo['LOCATION_COORD_SECTION']))
		assert (last_locKey_currently == self.num_visits_no_duplicates + len(self.bo['depotSection']))

		self.locations_used = deepcopy(self.bo['LOCATION_COORD_SECTION'])
		self.first_corner_ind_in_allcoords = None  # needed to put in locKeyInd in singleBatch case
		for obstacle_key, obstacle in self.obstacles_all.items():
			for i, corner_coords in enumerate(obstacle['corners']):
				if corner_coords in self.locations_used:
					raise Exception("joEx obstacle coordinate found which also exists as pick location")
				if obstacle_key == "1" and i == 0:
					self.first_corner_ind_in_allcoords = self.allcoords.index(corner_coords)
				self.locations_used.append(corner_coords)

	def add_locations_not_used_currently(self):
		"""
		add to bo. KEEP IT SIMPLE
		REQUIRES ENUMERATED INT INDICIES IN ALLCOORDS
		:return:
		"""

		last_locKey_currently = len(self.locKeyInd)
		new_locInd = 1  # starts here and will use it if it's not already used in locKeyInd
		for i, coords in enumerate(self.allcoords):
			if coords not in self.locations_used:
				if last_locKey_currently in self.locKeyInd:
					raise Exception("joEx trying to add a node key AGAIN to locKeyInd")
				flag_found_free_index = False
				while flag_found_free_index == False:
					if new_locInd not in self.locKeyInd.values():
						flag_found_free_index = True
					else:
						new_locInd += 1

				self.bo['LOCATION_COORD_SECTION'].append(coords)
				self.locations_used.append(coords)
				self.locKeyInd[str(last_locKey_currently)] = new_locInd
				last_locKey_currently += 1

		assert(last_locKey_currently == len(self.locKeyInd))
		for i in range(last_locKey_currently):
			if i not in self.locKeyInd.values():
				raise Exception("joEx something wrong with locKeyInd generation after permutation")

	def add_obstacles(self):
		"""
		ADD INDICES TO OBSTACLES
		:return:
		"""

		# k = self.num_visits_no_duplicates + len(self.bo['DEPOTS'])  # old
		last_locKey_currently = len(self.locKeyInd)  # the "key" that will next be created
		new_locInd = self.first_corner_ind_in_allcoords  # starts here and will use it if it's not already used in locKeyInd
		for j in range(1, len(self.obstacles_all) + 1):
			obst = self.obstacles_all[str(j)]
			for coords in obst['corners']:
				flag_found_free_index = False
				# while flag_found_free_index == False:
				# 	if new_locInd not in self.locKeyInd.values():
				# 		flag_found_free_index = True
				# 	else:
				# 		new_locInd += 1

				if str(last_locKey_currently) in self.locKeyInd or new_locInd in self.locKeyInd.values():
					raise Exception("joEx trying to add key or val that already exists")
				obst['inds'].append(last_locKey_currently)
				self.bo['LOCATION_COORD_SECTION'].append(coords)
				self.locKeyInd[str(last_locKey_currently)] = new_locInd
				last_locKey_currently += 1
				new_locInd += 1

		# CHECK THAT IND OF LAST OBSTACLE CORNER EXISTS
		if self.s['obstaclesType'] != 'NoObstacles':
			# TODO add test to make sure first obstacle location is last visit location + 1ish
			last_obst_corn_ind = self.obstacles_all[str(j)]['inds'][-1]
			if len(self.bo['LOCATION_COORD_SECTION']) != last_obst_corn_ind + 1:  # ube
				raise Exception("joExc mismatch between last obstacle ind and LOCATION_COORD_SECTION")

		# self.bo['LOCATION_COORD_SECTION']  : 102 items, index to 101: (72, 40)
		# self.obstacles_all: index to 101
		gg = 2 + 55 + 88  # 145  self.bo['LOCATION_COORD_SECTION'] 143 total
		aa = 5

	def test_all_locations_then_export_locKeyInd(self):

		# check that all locations are unique in locKeyInd
		locInds = list(self.locKeyInd.values())
		for ind in locInds:
			if locInds.count(ind) != 1:
				raise Exception("joEx non unique ind in locKeyInd found")

		if self.s['requestType'] == "storageAssignment":
			assert(len(self.allcoords) == len(self.bo['LOCATION_COORD_SECTION']))
			# OBS allcoords is NON-permutated, bo['LOC...'] IS permutated

			aa = 5
			pass
		else:
			pass

		# check that locKeyInd coords exist
		for locKey, ind in self.locKeyInd.items():
			temp_coord = self.allcoords[ind]

		# 3. Save locKeyInd
		with open(self.CLIENT_DATA_PATH + 'locKeyInd', 'wb') as f:
			pickle.dump(self.locKeyInd, f)

	def gen_allcoords(self):
		"""
		AT THIS POINT, DO ALLCOORDS ALREADY CONTAIN OBSTACLE CORNERS?
		ALLCOORDS is readonly
		:return:
		"""
		try:
			self._obs_gen.allcoords = self._obs_gen.allcoords + self._obs_gen.allowed_coords
		except:
			print("gen_allcoords failure")
			self._obs_gen.allcoords = self._obs_gen.allowed_coords

		for coords in self._obs_gen.allcoords:
			if self._obs_gen.allcoords.count(coords) != 1:
				raise Exception("joEx all coordinates not unique in allcoords")

	def bodict_to_AB_converter(self):
		"""
		GENERATES AB FROM THE INITED BO STRUCTURE
		:return:
		"""
		self.AB = {}

		box_template = {'pick_locs': [],
		                'available_from': 0,
		                'num_pick_locs': 0
		                }

		# BUILD THEM BOXES ===============
		for box_id in self.bo['ORDERS']:
			box_bo = self.bo['ORDERS'][box_id]

			box_ab = deepcopy(box_template)
			box_ab['available_from'] = box_bo['available_from']

			box_pls = box_bo['items']
			box_ab['num_pick_locs'] = len(box_pls)

			# LOOP OVER pls IN BOX
			for i in range(len(box_pls)):
				pl = box_pls[i]  # this is an int
				# time_avail_tsplib = self.bo['TIME_AVAIL_SECTION'][int(pl)]  # caution lots of int-str conversions

				box_ab['pick_locs'].append(pl)

			self.AB[box_id] = box_ab

		hgg = 7

	def AB_to_AB_list_converter(self):
		"""
		AB all is a sorted list version of AB
		OBS same reference for objects in AB_list and AB_all
		:return:
		"""
		self.AB_list = []  # stack

		for id in self.AB:  # put into stack

			box = self.AB[id]
			box['ORDER_ID'] = id  # id added since AB_list is a list

			self.AB_list.append(box)

		self.AB_list = sorted(self.AB_list, key=lambda k: k['available_from'])

	def bow_and_client_data_export(self):

		"""
		CREATES THE client-data.
		This data is probably identical for a storage assignment instance.
		"""

		# FIRST SAVE BO
		with open(self.folder_BDEV + 'bo_warehouse', 'wb') as f:
			pickle.dump(self.bo, f)

		# if self.s['requestType'] == 'storageAssignment':
		# 	DATA_PATH = "./client-data/bench/Slotting/optimizer-data/"
		# else:
		# 	self.CLIENT_DATA_PATH = "./client-data/bench/" + self.s['obstaclesType'] + "/optimizer-data/"

		print("deleting old optimizer-data ----")
		folder_name = self.CLIENT_DATA_PATH + "*"
		files = glob.glob(folder_name)
		for f in files:
			os.remove(f)

		print("digitization ----")
		print("allcoords...")

		# VISIT LOCATION COORDS  DEPR?
		# self._obs_gen.allcoords = self.bo['LOCATION_COORD_SECTION']  # new already done earlier

		# OBSTACLE COORDS  DEPR?-------------------------------------
		# _2_obstacle_gen.allcoords = []

		# DEPR?
		# for list in self._obs_gen.OBSTACLESANDDUMMYOBSTACLES:  # also append to allcoords
		# 	for tuple in list:
		# 		self._obs_gen.allcoords.append(tuple)

		if self.s['obstaclesType'] == 'No_obstacles':
			pass
		else:  # OBSTACLE COORDS ARE ADDED TO ALLCOORDS HERE. I THINK LOCATION_COORD_SECTION gets fixed by chance here bcs its a reference copy
			iii = len(self._obs_gen.allcoords)
			for rack_id in self._obs_gen.obstacles_all:  # also append to allcoords
				for tuple in self._obs_gen.obstacles_all[rack_id]['corners']:
					self._obs_gen.allcoords.append(tuple)  # OBS this probably also adds the coordinate to self.bo['LOCATION_COORD_SECTION']
					self._obs_gen.obstacles_all[rack_id]['inds'].append(iii)
					iii += 1
		for i, val in enumerate(self._obs_gen.allcoords):
			if type(val) != list:
				raise Exception("joEx allcoords must be list for bench")

		with open(self.CLIENT_DATA_PATH + 'allcoords', 'wb') as f:
			pickle.dump(self._obs_gen.allcoords, f)

		# BUILD DISTMAT (IN WHATEVER METRIC PROVIDED IN THE TSPLIB) NO ZERO-ROUNDING CHECK DONE HERE----------------------------------
		print("distmat....")
		if self.s['obstaclesType'] == 'None':
			self._obs_gen.distmat = np.zeros((len(self._obs_gen.allcoords), len(self._obs_gen.allcoords)), dtype=np.int64)
			for i in range(len(self._obs_gen.allcoords)):
				for j in range(len(self._obs_gen.allcoords)):
					if i == j:
						self._obs_gen.distmat[i, j] = 0
						self._obs_gen.distmat[j, i] = 0
					else:
						dist_x = abs(self._obs_gen.allcoords[i][0] - self._obs_gen.allcoords[j][0])
						dist_y = abs(self._obs_gen.allcoords[i][1] - self._obs_gen.allcoords[j][1])
						self._obs_gen.distmat[i, j] = np.sqrt(dist_x ** 2 + dist_y ** 2)

				if i % 100 == 0:
					print(str(i) + " out of " +str(self.bo['NUM_LOCATIONS']) + " done")
		else:
			self._obs_gen.run_graph_build()

		with open(self.CLIENT_DATA_PATH + 'distmat', 'wb') as f:
			pickle.dump(self._obs_gen.distmat, f)

		# BUILD locKeyInd NEW: THIS IS OVERWRITTEN LATER (NEEDED IN ORDER TO PUT RELEVANT LCOATIONS AT TOP OF TSPLIB)
		print("locKeyInd...")  # same regardless
		locKeyInd = {}
		for i in range(len(self._obs_gen.allcoords)):
			locKeyInd[str(i)] = i

		with open(self.CLIENT_DATA_PATH + 'locKeyInd', 'wb') as f:
			pickle.dump(locKeyInd, f)

		# BUILD SPNODESLIST, STARTENDNDARRAY (after first building spnodespath)
		print('SPNODESPATH...')
		if self.s['obstaclesType'] == 'None':
			self._obs_gen.SPNODEPATHS = {}
			for i in range(len(self._obs_gen.allcoords)):
				self._obs_gen.SPNODEPATHS[i] = {}
				for j in range(len(self._obs_gen.allcoords)):
					if i == j:
						self._obs_gen.SPNODEPATHS[i][j] = [i]
					else:
						self._obs_gen.SPNODEPATHS[i][j] = [i, j]

			# code from p4_split_SPNODESPATHS
			self._obs_gen.startendndarray = np.ndarray([len(self._obs_gen.allcoords), len(self._obs_gen.allcoords), 2],
			                                           dtype=np.uint32)  # OBS it's read with upper bound exclusive
			listo = []

			for i in range(0, len(self._obs_gen.allcoords)):
				for j in range(0, len(self._obs_gen.allcoords)):
					startpos = len(listo)
					listo += self._obs_gen.SPNODEPATHS[i][j]
					endpos = len(listo)
					self._obs_gen.startendndarray[i, j, 0] = startpos
					self._obs_gen.startendndarray[i, j, 1] = endpos

			self._obs_gen.spnodeslist = np.asarray(listo).flatten().astype(np.int16)

		else:
			pass  # they are created within the obs_gen run_graph_build function

		with open(self.CLIENT_DATA_PATH + 'startendndarray', 'wb') as f:
			pickle.dump(self._obs_gen.startendndarray, f)

		with open(self.CLIENT_DATA_PATH + 'spnodeslist', 'wb') as f:
			pickle.dump(self._obs_gen.spnodeslist, f)

	def export_AB(self):
		"""
		Saves the Available Boxes dicts (WHY?)
		:return:
		"""
		print("saving files...")
		# dir_output = './benchmarking/BDEV/'
		# dir_output = './benchmarking/files/bench/'

		# with open(dir_output + 'bo_gen0', 'wb') as f:
		# 	pickle.dump(self.bo, f)

		# with open(self.folder_BDEV + 'AB', 'wb') as f:
		# 	pickle.dump(self.AB, f)

		with open(self.folder_BDEV + 'AB_list', 'wb') as f:
			pickle.dump(self.AB_list, f)

	def export_AB_tsplib_dict(self):
		"""
		similar to bodict but this includes a bunch of tsplib bloat (not really needed) i.e. kept separate
		THIS IS SAVED AS A JSON THAT CAN THEN BE USED FOR REPRODUCIBILITY AND CONVERTED TO TSPLIB
		duration section not used
		This function only generates a json.  export_tsplib in OBP_simulator generates the .txt
		"""

		di = deepcopy(self.bo)

		if self.s['requestType'] == "singlebatch" or self.s['requestType'] == "MULTIBATCH_OPTIMIZATION":
			problem_type = "OBP"
		elif self.s['requestType'] == "storageAssignment":
			problem_type = "SLAP"
		else:
			raise Exception("FAAAA")

		di["HEADER"] = {"VERSION": "VRPTEST 1.0",
		                "COMMENTS": {"descr": "Modified tsplib for the " + problem_type,
		                             "Best known objective": "",
		                             "Computational time (s)": ""}
		                }
		di["NAME"] = self._tsplib_name
		di["NUM_DEPOTS"] = self.bo['NUM_DEPOTS']
		di["NUM_CAPACITIES"] = 1
		di["NUM_VISITS"] = self.bo['NUM_VISITS']
		di["NUM_VEHICLES"] = self.s['numVehicles']
		di["CAPACITIES"] = self.s['mobileUnitCapacities']['numOrders']  # NOT SCALABLE
		di["DATA_SECTION"] = ""
		di["DEPOTS"] = self.bo['DEPOTS']
		# di["DEPOT_LOCATION_SECTION"] = self.bow["DEPOT_LOCATION_SECTION"]

		# DEMAND_SECTION = {}
		VISIT_LOCATION_SECTION = {}

		# last_visit_loc_i =
		if len(self.obstacles_all) > 1:
			pass

		for i in range(len(di["DEPOTS"]), self.num_visits_no_duplicates + len(di["DEPOTS"])):
			# DEMAND_SECTION[str(i)] = "-1"
			VISIT_LOCATION_SECTION[str(i)] = str(i)

		# test that above is correct
		for order_id, order in self.AB.items():
			assert(order['pick_locs_in_keydict'] == order['pick_locs'])  # might be removed later if sorting not to be used.
			for pl in order['pick_locs_in_keydict']:
				loc = int(VISIT_LOCATION_SECTION[pl])  # test that pick loc KEY exists
				test_loc = self.bo['LOCATION_COORD_SECTION'][loc]  # test that location exists
		aa = 6

		# di["DEMAND_SECTION"] = DEMAND_SECTION
		di["NUM_LOCATIONS"] = len(self.bo['LOCATION_COORD_SECTION'])  # hence num_locations has nothing to do with obstracles, BUT LOCATION_COORD_SECTION does
		if self.s['requestType'] != 'storageAssignment':
			di["NUM_LOCATIONS"] = self.num_visits_no_duplicates + len(di["DEPOTS"]) + len(self.obstacles_all) * 4

		di["LOCATION_COORD_SECTION"] = {}  # by now obstacles have been added
		for i in range(0, di["NUM_LOCATIONS"]):  # ube
			x = self.bo['LOCATION_COORD_SECTION'][i][0]
			y = self.bo['LOCATION_COORD_SECTION'][i][1]
			di["LOCATION_COORD_SECTION"][str(i)] = (str(x), str(y))

		di["VISIT_LOCATION_SECTION"] = VISIT_LOCATION_SECTION
		di["TIMESTEP"] = "1"

		ORDERS = {}
		TIME_AVAIL_SECTION = {}  # OBS THIS WILL BE DIFFERENT IF ORDER-INTEGRITY NOT REQUIRED
		for i in range(1, len(self.bo['ORDERS']) + 1):  # assumes orders are numbered starting at 1

			box = self.bo['ORDERS'][str(i)]
			TIME_AVAIL_SECTION[str(i)] = str(box['available_from'])

			ORDERS[str(i)] = box['items']

		di['ORDERS'] = ORDERS
		di['TIME_AVAIL_SECTION'] = TIME_AVAIL_SECTION

		if self.s['obstaclesType'] == 'None':
			pass
		else:
			di['OBSTACLES'] = {}
			for obstacle_key in self.obstacles_all:
				di['OBSTACLES'][obstacle_key] = []
				for ind in self.obstacles_all[obstacle_key]['inds']:
					di['OBSTACLES'][obstacle_key].append(str(ind))

		with open(self.folder_BDEV + 'tsplib_di_temp', 'wb') as f:  # not saved as json here since it's just temp anyway
			pickle.dump(di, f)

		# with open(self.folder_BDEV + 'specs', 'wb') as f:  # not saved as json here since it's just temp anyway
		# 	pickle.dump(self.s, f)

		aa = 5

	def visualize_coords(self):

		"""
		OBS THIS VISUALIZES THE POSSIBLE COORDINATES IN A DIGITIZED WAREHOUSE,
		NOT ACTUAL COORDINATES IN A SPECIFIC INSTANCE (THESE ARE GENERATED AT A LATER STAGE)
		:return:
		"""

		import matplotlib.pyplot as plt

		fig = plt.figure()
		ax = fig.subplots()

		# OBSTACLES
		xs = []
		ys = []
		for rect_coords in self._obs_gen.OBSTACLESANDDUMMYOBSTACLES:
			for tuple in rect_coords:
				xs.append(tuple[0])
				ys.append(tuple[1])
		ax.plot(xs, ys, '+', markersize=8, color='red')

		# PICK LOCS
		xs = []
		ys = []
		for tuple in self._obs_gen.allcoords:
			xs.append(tuple[0])
			ys.append(tuple[1])

		ax.plot(xs, ys, 'x', markersize=8, color='black')

		for i in range(0, len(self.s['depotSection'])):
			ax.plot(xs[i], ys[i], 's', markersize=15, color='blue')

		plt.show()

# with open('./bo_files/bo_c75D', 'rb') as f:
# 	bodict = pickle.load(f)

#

if __name__ == "__main__":

	# OBSTACLES_TYPE = 'SingleRack'

	with open("./benchmarking/specs_skeletons/s_temp.json", "r") as f:
		specs = json.load(f)

	bog = Generator(specs, EXPORT_PATH_OUTER=None, digit_type='digitize_warehouse', just_visualize=True)  # HHEEE
	# bog = Generator(specs, digit_type='digitize_AB', just_visualize=False)  # HHEEE

