'''
Does everything. _4_ and _3_ do things individually.
allcoords and all other client data EXCEPT locKeyInd are read-only once created in the digitization
An identified problem here is that it is based on orders, not products. This makes it more complex for SLAP
'''

import os
import glob
import pickle
import json
import random
# random.seed(2)
import math
import numpy as np
import uuid
from copy import deepcopy
import benchmarking.utils_benchmarking.graph_gen_w_obstacles as _2_og
from benchmarking.utils_benchmarking import repr_tsplib
from model.storage_assignment.SLAP_wrapper import SLAP_wrapper


# MOVED TO specs_skeletons
# bodict_skeleton = {
# 	'TYPE': 'OBP',
# 	'NUM_VISITS': '',
# 	'NUM_LOCATIONS': '',
# 	'LOCATION_COORD_SECTION': [],
# 	'ORDERS': {},
# 	'DEPOTS': '',
# 	'NUM_DEPOTS': None,
# }
DEBUGGING = False
# JUST_VISUALIZE = False

class Generator:
	"""
	Is either launched to generate a warehouse (from main below), i.e. client-data once AND
	the parent tsplib in tsplibfiles.
	Or it is used to generate orders from a simulator e.g. OBP_simulator
	Creates AB (the dict used in the OBP loop) and bodict (bodict contains everything needed)
	Requires a obstacle_gen placeholder even if obstacles aren't there.
	"""

	def __init__(self, specs, EXPORT_PATH_OUTER):  # , random_seed=None):
		"""
		digit_warehouse: WAREHOUSE ONLY DIGITIZED ONCE. bo is a short name for tsplib_parent
		TODO: longterm: digitize_O should be a child class, not a set of separate functions.
		:param just_visualize: Does not save any files only visualizes instance
		:param random_seed: random seed from previous instance used to reproduce tsplib
		"""

		with open('benchmarking/specs_skeletons/tsplib_parent_template.json', 'r') as f:
			self.bo = json.load(f)

		# random.seed(specs['randomSeed'])

		self.s = specs
		self.bo['depotSection'] = self.s['depotSection']
		self.EXPORT_PATH_OUTER = EXPORT_PATH_OUTER

		self.s['numVehicles'] = self.s['numOrders'] // self.s['mobileUnitCapacities']['numOrders'] + 1

		if self.s['requestType'] == 'storageassignment':
			self.CLIENT_DATA_PATH = "./client-data/bench/" + specs['obstaclesType'] + "/"
			self.path_local = specs['path_local']
		elif self.s['requestType'] == 'singlebatch' or self.s['requestType'] == 'multibatch':
			self.CLIENT_DATA_PATH = "./client-data/bench/" + self.s['obstaclesType'] + "/"
			self.path_local = specs['path_local']
		else:
			raise Exception("joEx wrong requestType")

	def run(self, digit_type=None, just_visualize=False):

		if digit_type == 'digitize_warehouse':
			self.graph_module_init()
			self.depots_and_allcoords_init()
			self.get_allcoords_no_obstacles()

			if just_visualize is False:
				self.gen_all_client_data()
				self.export_meta_and_client_data()
				self.export_required_tsplib_parent_fields()
				self.visualize_coords(export=True)
			else:
				self.visualize_coords(export=False)

		elif digit_type == 'digitize_O':  # only for OBP (orders are generated here)

			self.load_data()  # previously digitized data LOADED FROM BDEV
			self.O, self.SKUs_all = self.gen_orders_and_skus_no_locations()
			self.orders_extra_modding()
			self.duplicate_visits()

			self.SKUs_to_slot0, _ = self.get_SKUs_to_slot_from_O()
			self.sd = self.location_assignment_zoning(self.SKUs_to_slot0)
			self.tsplib_name()

			# self.export_AB()  # only needed for debug
			if self.sd != None:
				self.di = self.build_AB_tsplib_dict(export=False)

		elif digit_type == 'load_previous_instance':
			self.load_data()
			with open(self.path_local + 'instances/' + self.s['nameTsplib'] + '/' + self.s['nameTsplib'] + '.json', 'r') as f:
				self.di = json.load(f)

			# REBUILD ORDERS =============================
			self.O = {}
			for order_id, order in self.di['ORDERS'].items():

				with open('./docs/schemas/common/bo/order_template.json', 'r') as f:
					o = json.load(f)
				o['orderId'] = order_id

				o['orderPickItems']['SKUs'] = order
				for sku_id in order:
					o['orderPickItems']['locations'].append(self.di['VISIT_LOCATION_SECTION'][sku_id])
				self.O[order_id] = o

	def tsplib_name(self):
		if self.s['nameTsplib'] == None:
			self._tsplib_name = "c" + str(self.bo['NUM_VISITS']) + "_" + str(uuid.UUID(int=self.s['randomSeed']))[-4:]
		# _, folder_names, file = os.walk(self.EXPORT_PATH_OUTER).__next__()
		# if self._tsplib_name in folder_names:
		# 	raise Exception("joEx the tsplib name already exists!")
		else:
			self._tsplib_name = self.s['nameTsplib']

	def graph_module_init(self):
		"""
		possibleVisitLocs are used here bcs it's used to generate allcoords?
		:return:
		"""

		self._graph_gen = _2_og.GraphGen(self.s)
		self._graph_gen.define_obstacles(self.s['obstaclesType'], self.s['possibleVisitLocs'], DEBUGGING)
		self._graph_gen.gen_OBSTACLESANDDUMMYOBSTACLES()  # should be removed eventually

		self.bo['num_pick_locs_warehouse'] = len(self._graph_gen.allowed_coords)  # should not include corners

	def depots_and_allcoords_init(self):
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
			# self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['0'])
			self.bo['DEPOTS'] = ['0']  # only inds are shown
			self._graph_gen.allcoords_no_obstacles = [self.s['depotSection']['0']]
			# self.bo["DEPOT_LOCATION_SECTION"] = {'0': '0'}

			aa =5
		# elif self.s['DEPOTS'] == "default_1":  # DEPR?
		# 	# while good_candidate ...
		# 	self.bo['LOCATION_COORD_SECTION'].append(default_loc)  # TODO randint
		# 	self.bo['DEPOTS'] = ['0']
		elif len(self.s['depotSection']) == 2:
			# while good_candidate ...
			# self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['0'])
			# self.bo['LOCATION_COORD_SECTION'].append(self.s['depotSection']['1'])
			self._graph_gen.allcoords_no_obstacles = [self.s['depotSection']['0'], self.s['depotSection']['1']]  # new
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


		# with open(path_local + 'AB_all', "rb") as f:
		# 	self.AB_all = pickle.load(f)
		#
		# with open('./benchmarking/bench_res', "rb") as f:
		# 	self.bench_res = pickle.load(f)

		with open(self.path_local + 'tsplib_parent.json', "r") as f:
			self.bow = json.load(f)

		# TEST DEPOTS
		# if self.bow['depotSection'] != self.s['depotSection']:   # this is inited (again) in OBP_simulator
		# 	raise Exception("joExc NUM DEPOTS IS HARDCODED when the warehouse is generated. "
		# 	                "Check the specs in OBP_simulator, needs to correspond. This is to verify that you"
		# 	                "are diligent when running OBP_simulator")

		# # TEST OBSTACLES TYPE
		# if self.bow['obstaclesType'] != self.s['obstaclesType']:   # this is inited (again) in OBP_simulator
		# 	raise Exception("joExc NUM DEPOTS IS HARDCODED when the warehouse is generated. "
		# 	                "Check the specs in OBP_simulator, needs to correspond. This is to verify that you"
		# 	                "are diligent when running OBP_simulator")

		# self.bo['LOCATION_COORD_SECTION'] = deepcopy(self.bow['LOCATION_COORD_SECTION'])  # adds depot info
		del self.bo['LOCATION_COORD_SECTION']
		self.bo['DEPOTS'] = self.bow['DEPOTS']

		with open(self.path_local + 'meta/obstacles_all.json', "r") as f:
			self.obstacles_all = json.load(f)

		bench_type = self.s['obstaclesType']
		if self.s['requestType'] == "storageassignment":
			bench_type = 'bench'

		# LOAD DATA FROM DIGITAL TWIN =================
		# self.CLIENT_DATA_PATH = "./client-data/" + bench_type + "/Slotting/optimizer-data/"
		with open(self.CLIENT_DATA_PATH + 'allcoords', "rb") as f:
			self.allcoords = pickle.load(f)

		with open(self.CLIENT_DATA_PATH + 'locKeyInd.json', "r") as f:
			self.locKeyInd = json.load(f)

		with open(self.CLIENT_DATA_PATH + 'distmat', "rb") as f:
			self.distmat = pickle.load(f)

		self.allcoords_no_obstacles = None
		# if self.s['requestType'] == 'storageassignment':
		with open(self.path_local + 'meta/allcoords_no_obstacles', "rb") as f:
			self.allcoords_no_obstacles = pickle.load(f)

	# with open(self.CLIENT_DATA_PATH + 'locKeyInd', "rb") as f:  # NEEDED FOR SLOTTING
	# 	self.locKeyInd = pickle.load(f)

	def modify_tsplib_for_SLAP(self):
		"""
		Some orders lose their locations and are marked for slotting
		Feb 8 2022: req updated according to latest schema.
		"""
		O_S = deepcopy(self.O)
		SKUs_all = {}
		prob_unassigned = self.s['dynamicity']['percDynamic'] / 100
		SKUs_to_slot1 = {}  # CHANGED TO DICT
		for order_id, order in O_S.items():
			for i in range(len(order['orderPickItems']['SKUs'])):
				SKU = order['orderPickItems']['SKUs'][i]
				SKUs_all[SKU] = {"ind_current": order['orderPickItems']['locations'][i],
								 "zone": None,
								 "SLAP_type": "preassigned"}

				if random.random() < prob_unassigned:
					order['orderPickItems']['locations'][i] = None
					self.di['VISIT_LOCATION_SECTION'][SKU] = None  # SKU_id -> location
					SKUs_to_slot1[SKU] = {"location": None, "zone": None}  # will try to put the sku in one of the locations
					SKUs_all[SKU]['ind_current'] = None  # overwritten
					SKUs_all[SKU]['SLAP_type'] = "unassigned"  # overwritten

		if len(SKUs_to_slot1) < 1:  # select first sku and make it slappable
			O_S['1']['orderPickItems']['locations'][0] = None
			SKU = O_S['1']['orderPickItems']['SKUs'][0]
			self.di['VISIT_LOCATION_SECTION'][SKU] = None
			SKUs_to_slot1[SKU] = {"location": None, "zone": None}  # 0 is default

		# for sku_id, sku in SKUs_to_slot1.items():  # find primary zone for sku
		# 	sku_zone_i = [i for i, zone in enumerate(self.s['slottingZones']) if sku_id in zone["SKUs"]][0]  # only take first zone since item can only appear in 1 zone
		# 	sku['zone'] = sku_zone_i  # might be changed later if no locations in primary zone found

		return O_S, SKUs_to_slot1, SKUs_all

	def gen_orders_and_skus_no_locations(self):
		"""
		New: just uses the template
		The SKUs are provided here, but locations are provided later during slotting
		At this stage the orders get unique SKUs. For many orders use 1 SKU/order and then duplicate with e.g. 400%
		OBS THE NAMES OF THE SKU'S MUST BE A RANGE E.G. '2', '3' ...
		:return:
		"""

		with open('./docs/schemas/common/bo/order_template.json', 'r') as f:
			order_template = json.load(f)  # OBS does not include available_from

		# self.bo['orders'] = {}  # uses template
		O = {}  # uses template
		SKUs_all = {}  # SKUs_all['1'] = {"location": "notAssigned", "zone": None}

		item_i = 1
		start_c = 1
		if len(self.s['depotSection']) == 2:
			item_i = 2  # when there are two depots
			start_c = 2
		for i in range(1, self.s['numOrders'] + 1):
			order_new = deepcopy(order_template)
			num_items_in_order = random.randint(self.s['itemsPerBoxLow'], self.s['itemsPerBoxHigh'])

			rr = range(item_i, item_i + num_items_in_order)
			order_new['orderPickItems']['SKUs'] = [str(number) for number in rr]
			order_new['orderId'] = str(i)
			# self.bo['orders'][str(i)] = {'SKUs': [str(x) for x in rr]}
			O[str(i)] = order_new
			for number in rr:
				SKUs_all[str(number)] = {"location": "notAssigned", "zone": None}  # change notAssigned to None?

			item_i += len(rr)

		# if self.s['requestType'] != "storageassignment":
		# 	self.bo['NUM_LOCATIONS'] = item_i + len(self.obstacles_all) * 4 # same number as order-pick locs + corners
		# else:  # all locations + corners
		# 	self.bo['NUM_LOCATIONS'] = self.bow['num_pick_locs_warehouse'] + len(self.obstacles_all) * 4 # march 30 2021

		self.bo['NUM_VISITS'] = item_i - 1  # single depot
		if len(self.s['depotSection']) == 2:
			self.bo['NUM_VISITS'] = item_i - 2
		self.num_visits_no_duplicates = deepcopy(self.bo['NUM_VISITS'])
		print("total number of items: " + str(item_i))

		return O, SKUs_all

	def orders_extra_modding(self):
		"""
		Basic dynamicity and DOESNT SEEM TO DO shuffling of some products (BUT SHOULD) (TO BREAK ZONES)
		VERY CRUDE CURRENTLY FOR SLAP. SEEMS TO JUST SPLIT ORDERS 50-50 BETWEEN 2 TIME-STEPS
		Obs. Also, this just makes optimization harder and visualizations look more messy.
		:return:
		"""
		time_chunks = np.array_split(range(1, self.s['numOrders'] + 1), self.s['dynamicity']['numTimeSteps'])  # UBE
		_orders_available_from = [list(x) for x in time_chunks]  # denumpy
		_orders_available_from.insert(0, [0])  # MAYBE NOT. NEEDED TO PROVIDE STARTING POINT FOR ITERATION BELOW

		if self.s['numItemsToMove'] > 0:  # like duplicate items but more shufflish
			time_step_from = random.randint(1, max(1, self.s['dynamicity']['numTimeSteps'] - 1))  # max for single slotting zone case
			time_step_to = max(1, time_step_from - 1)  # to prevent slots from being broken too much
			num_items_to_move = 2  # random.randint(1, _boxes_available_from[time_step_from] - 1)
			items_to_move = random.sample(_orders_available_from[time_step_from], num_items_to_move)
			for item in items_to_move:  # seems ok with single timestep
				_orders_available_from[time_step_to].append(item)
				_orders_available_from[time_step_from].remove(item)  # only removes 1 at a time

		for t in range(1, len(_orders_available_from)):  # t = timestep
			orders_at_t = _orders_available_from[t]
			for id in orders_at_t:
				self.O[str(id)]['available_from'] = t

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
			from_key = random.choice(list(self.O.keys()))
			item = random.choice(self.O[from_key]['orderPickItems']['SKUs'])
			to_key = random.choice(list(self.O.keys()))
			self.O[to_key]['orderPickItems']['SKUs'].append(item)
			self.bo['NUM_VISITS'] += 1  # SINCE IT MAY BE DIFFERENT VEHICLES THAT VISIT THE SKU
			self.duplicate_items[item] = {"coords": None}
		aa = 5

	def get_SKUs_to_slot_from_O(self):
		"""
		TODO: CHANGE SKUs_to_slot TO DICT. LIST IS NOW DEPRECATED (for various reasons)
		The input to SLAP opt is a list of products (SKUs), not orders.
		Both Zoner and DPSO will use distmat and weights, not orders.
		"""

		SKUs_to_slot0 = []  # don't do time_step 2 BUT NEW: WILL DO IT FOR DUPLICATES
		SKUs_to_slot1 = []
		for order_id, order in self.O.items():
			for sku_id in order['orderPickItems']['SKUs']:
				if order['available_from'] == 1 and sku_id not in SKUs_to_slot0:
					SKUs_to_slot0.append(sku_id)
				elif order['available_from'] == 2:
					SKUs_to_slot1.append(sku_id)

		return SKUs_to_slot0, SKUs_to_slot1

	def location_assignment_zoning(self, SKUs_to_slot):

		sd = {"allcoords_no_obstacles": self.allcoords_no_obstacles,
			  "locKeyInd": self.locKeyInd,
			  "SKUs_all": self.SKUs_all,
			  "SKUs_to_slot": SKUs_to_slot,
			  "slottingZones": self.s['slottingZones'],
			  "O": self.O,
			  "W": None,
			  "distmat": self.distmat,
			  }

		_st_gen = StorageAssignmentOptimizerWrapper(self.s, sd)  # no need to have an instance here (it's just used to generate SKU's with lcos here
		_st_gen.run()
		if _st_gen._z.general_slotting_failure == True:
			return None

		# map the locations in _st_gen to orders
		for o_id, o in self.O.items():
			SKUs_o = o['orderPickItems']['SKUs']
			locs_o = o['orderPickItems']['locations']
			for i, sku_id in enumerate(SKUs_o):  # THIS IS, AND MUST BE, ORDERED
				loc = self.SKUs_all[sku_id]['location']
				locs_o.append(loc)
		return sd

	def coordinates_AB(self):

		"""
		DEPRECATED (SLAP optimizer used instead)
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

			for pl_ind in box['SKUs']: # THIS GIVES COORDS TO PICK ITEMS

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
						for slot_key, slot in self._z.zones.items():
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
		DEPRECATED
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

	def get_locations_used(self):
		"""
		NEEDS BIG REFACTOR SINCE LOCATION_COORD_SECTION LOGIC BEEN CHANGED
		DOCUMENT IT G* D*
		Returns
		-------

		"""

		# last_locKey_currently = len(self.locKeyInd)
		assert (last_locKey_currently == max([int(x) for x in self.locKeyInd]) + 1)  # check above. UBE

		# BELOW IS NOW PENDING DELETION SINCE LOCATIONS ARE MADE CONSTANT
		# assert (last_locKey_currently == len(self.bo['LOCATION_COORD_SECTION']))
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
		DEPRECATED: OBSTACLES IN NEW VERSION HAVE ALREADY GOTTEN THEIR INDICIES
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


		# self.bo['LOCATION_COORD_SECTION']  : 102 items, index to 101: (72, 40)
		# self.obstacles_all: index to 101
		gg = 2 + 55 + 88  # 145  self.bo['LOCATION_COORD_SECTION'] 143 total
		aa = 5

	def test_all_locations_then_export_locKeyInd(self):
		"""
		PROBABLY DEPRECATED, OR AT LEAST REDUNDANT SINCE locKeyInd IS SO SIMPLE NOW
		"""
		# CHECK THAT IND OF LAST OBSTACLE CORNER EXISTS
		if self.s['obstaclesType'] != 'NoObstacles' or self.s['obstaclesType'] == 'No_obstacles':
			# TODO add test to make sure first obstacle location is last visit location + 1ish
			last_obst_corn_ind = self.obstacles_all[str(j)]['inds'][-1]
			if len(self.bo['LOCATION_COORD_SECTION']) != last_obst_corn_ind + 1:  # ube
				raise Exception("joExc mismatch between last obstacle ind and LOCATION_COORD_SECTION")

		# check that all locations are unique in locKeyInd
		locInds = list(self.locKeyInd.values())
		for ind in locInds:
			if locInds.count(ind) != 1:
				raise Exception("joEx non unique ind in locKeyInd found")

		if self.s['requestType'] == "storageassignment":
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

	def get_allcoords_no_obstacles(self):
		"""
		ALLCOORDS is generated further below
		:return:
		"""
		try:  # adds depot coords + allowed
			self._graph_gen.allcoords_no_obstacles = self._graph_gen.allcoords_no_obstacles + self._graph_gen.allowed_coords
		except:
			print("WARNING: gen_allcoords failure")
			self._graph_gen.allcoords_no_obstacles = self._graph_gen.allowed_coords

		for coords in self._graph_gen.allcoords_no_obstacles:
			if self._graph_gen.allcoords_no_obstacles.count(coords) != 1:
				raise Exception("joEx all coordinates not unique in allcoords")

	# DEPR (or at least should be)
	# def bodict_to_AB_converter_new(self):
	# 	"""
	# 	TOTALLY DEPRECATED (IT WAS STUPID AND REDUNDANT FROM BEGINNING: USE ORDER TEMPLATE IN BO INSTEAD!!!)
	# 	GENERATES AB FROM THE INITED BO STRUCTURE
	# 	:return:
	# 	"""
	# 	self.AB = {}
	#
	#
	# 	#
	# 	# box_template = {'SKUs': [],
	# 	#                 'available_from': 0,
	# 	#                 'num_SKUs': 0
	# 	#                 }
	#
	# 	# BUILD THEM BOXES ===============
	# 	for order_id, order in self.bo['ORDERS'].items():
	# 		# box_bo = self.bo['ORDERS'][box_id]
	#
	# 		box_ab = deepcopy(box_template)
	# 		box_ab['available_from'] = order['available_from']
	#
	# 		box_SKUs = order['SKUs']
	# 		box_ab['num_pick_locs'] = len(box_SKUs)  # should be number of picks, not pick locs
	#
	# 		# LOOP OVER pls IN BOX
	# 		for i in range(len(box_SKUs)):
	# 			sku = box_SKUs[i]  # this is an int
	# 			# time_avail_tsplib = self.bo['TIME_AVAIL_SECTION'][int(pl)]  # caution lots of int-str conversions
	#
	# 			box_ab['SKUs'].append(sku)
	#
	# 		self.AB[order_id] = box_ab
	#
	# 	hgg = 7

	# def AB_to_AB_list_converter(self):
	# 	"""
	# 	AB all is a sorted list version of AB
	# 	OBS same reference for objects in AB_list and AB_all
	# 	:return:
	# 	"""
	# 	self.AB_list = []  # stack
	#
	# 	for id in self.AB:  # put into stack
	#
	# 		box = self.AB[id]
	# 		box['ORDER_ID'] = id  # id added since AB_list is a list
	#
	# 		self.AB_list.append(box)
	#
	# 	self.AB_list = sorted(self.AB_list, key=lambda k: k['available_from'])

	def gen_all_client_data(self):

		# DELETE OLD DATA TO ENSURE NO MESS UP =======================
		print("deleting old optimizer-data ----")
		folder_name = self.CLIENT_DATA_PATH + "*"
		files = glob.glob(folder_name)
		for f in files:
			if f == './client-data/bench/HERE/config.json':
				continue
			os.remove(f)

		print("saving client-data to : " + str(self.CLIENT_DATA_PATH))

		# BUILD locKeyInd =======================
		print("locKeyInd...")  # same regardless
		self.locKeyInd = {}
		for i in range(0, len(self._graph_gen.allcoords_no_obstacles)):  # NOTE 0 IS A MUST!!!
			self.locKeyInd[str(i)] = i
		max_locKeyInd = i

		# ALLCOORDS WITH OBSTACLES FINALIZED HERE ===================
		print("allcoords...")
		self._graph_gen.allcoords = deepcopy(self._graph_gen.allcoords_no_obstacles)
		if self.s['obstaclesType'] == 'No_obstacles' or self.s['obstaclesType'] == 'No_obstaclesL':
			pass
		else:  # OBSTACLE COORDS ARE ADDED TO ALLCOORDS HERE. I THINK LOCATION_COORD_SECTION gets fixed by chance here bcs its a reference copy
			iii = len(self._graph_gen.allcoords)
			assert(iii == max_locKeyInd + 1)  # inds for obstacles start where locKeyInd ends
			for i in range(1, len(self._graph_gen.obstacles_all) + 1):  # also append to allcoords
				for tuple in self._graph_gen.obstacles_all[str(i)]['corners']:
					self._graph_gen.allcoords.append(tuple)
					self._graph_gen.obstacles_all[str(i)]['inds'].append(iii)
					iii += 1
		for i, val in enumerate(self._graph_gen.allcoords):
			if type(val) != list:
				raise Exception("joEx allcoords must be list for bench")

		# TEST CORRESPONDENCE BETWEEN num_pick_locs_warehouse and obstacles_all
		if len(self._graph_gen.obstacles_all) > 0:
			obstacles_first_index_should_be = self.bo['num_pick_locs_warehouse'] - 1 + len(self.bo['DEPOTS']) + 1
			first_obstacles_all_ind = self._graph_gen.obstacles_all['1']['inds'][0]
			if obstacles_first_index_should_be != first_obstacles_all_ind:
				raise Exception("joEx obstacles_all first ind does not seem correct")

		# BUILD DISTMAT (IN WHATEVER METRIC PROVIDED IN THE TSPLIB) NO ZERO-ROUNDING CHECK DONE HERE----------------------------------

		if self.s['obstaclesType'] == 'NoObstacles' or self.s['obstaclesType'] == 'NoObstaclesL':

			print("distmat no obstacles....")
			self._graph_gen.distmat = np.zeros((len(self._graph_gen.allcoords), len(self._graph_gen.allcoords)),
											   dtype=np.float16)
			for i in range(len(self._graph_gen.allcoords)):
				for j in range(len(self._graph_gen.allcoords)):
					if i == j:
						self._graph_gen.distmat[i, j] = 0
						self._graph_gen.distmat[j, i] = 0
					else:
						dist_x = abs(self._graph_gen.allcoords[i][0] - self._graph_gen.allcoords[j][0])
						dist_y = abs(self._graph_gen.allcoords[i][1] - self._graph_gen.allcoords[j][1])
						self._graph_gen.distmat[i, j] = np.sqrt(dist_x ** 2 + dist_y ** 2)

				if i % 100 == 0:
					print(str(i) + " out of " + str(self.bo['NUM_LOCATIONS']) + " done")

			print("spnodespaths no obstacles...")
			self._graph_gen.SPNODEPATHS = {}
			for i in range(len(self._graph_gen.allcoords)):
				self._graph_gen.SPNODEPATHS[i] = {}
				for j in range(len(self._graph_gen.allcoords)):
					if i == j:
						self._graph_gen.SPNODEPATHS[i][j] = [i]
					else:
						self._graph_gen.SPNODEPATHS[i][j] = [i, j]

			# code from p4_split_SPNODESPATHS
			self._graph_gen.startendndarray = np.ndarray(
				[len(self._graph_gen.allcoords), len(self._graph_gen.allcoords), 2],
				dtype=np.uint32)  # OBS it's read with upper bound exclusive
			listo = []

			for i in range(0, len(self._graph_gen.allcoords)):
				for j in range(0, len(self._graph_gen.allcoords)):
					startpos = len(listo)
					listo += self._graph_gen.SPNODEPATHS[i][j]
					endpos = len(listo)
					self._graph_gen.startendndarray[i, j, 0] = startpos
					self._graph_gen.startendndarray[i, j, 1] = endpos

			self._graph_gen.spnodeslist = np.asarray(listo).flatten().astype(np.int16)
		else:
			self._graph_gen.run_graph_build()

		# OLD
		# # BUILD SPNODESLIST, STARTENDNDARRAY (after first building spnodespath)
		# print('SPNODESPATH...')
		# if self.s['obstaclesType'] == 'None':
		# 	self._graph_gen.SPNODEPATHS = {}
		# 	for i in range(len(self._graph_gen.allcoords)):
		# 		self._graph_gen.SPNODEPATHS[i] = {}
		# 		for j in range(len(self._graph_gen.allcoords)):
		# 			if i == j:
		# 				self._graph_gen.SPNODEPATHS[i][j] = [i]
		# 			else:
		# 				self._graph_gen.SPNODEPATHS[i][j] = [i, j]
		#
		# 	# code from p4_split_SPNODESPATHS
		# 	self._graph_gen.startendndarray = np.ndarray(
		# 		[len(self._graph_gen.allcoords), len(self._graph_gen.allcoords), 2],
		# 		dtype=np.uint32)  # OBS it's read with upper bound exclusive
		# 	listo = []
		#
		# 	for i in range(0, len(self._graph_gen.allcoords)):
		# 		for j in range(0, len(self._graph_gen.allcoords)):
		# 			startpos = len(listo)
		# 			listo += self._graph_gen.SPNODEPATHS[i][j]
		# 			endpos = len(listo)
		# 			self._graph_gen.startendndarray[i, j, 0] = startpos
		# 			self._graph_gen.startendndarray[i, j, 1] = endpos
		#
		# 	self._graph_gen.spnodeslist = np.asarray(listo).flatten().astype(np.int16)
		#
		# else:
		# 	pass  # they are created within the obs_gen run_graph_build function

		aa = 5

	def export_meta_and_client_data(self):

		"""
		bow is the tsplib skeleton that will later be built on for specific instances.
		tsplib_parent is generated with the LOCATION_COORD_SECTION
		CREATES THE client-data. PATH is detected based on obstacle type name.
		This data is probably identical for a storage assignment instance.
		"""


		# BO SAVING HAS BEEN MOVED TO AFTER ALLCOORDS, SINCE THEY ARE FINISHED HERE

		# if self.s['requestType'] == 'storageAssignment':
		# 	DATA_PATH = "./client-data/bench/Slotting/optimizer-data/"
		# else:
		# 	self.CLIENT_DATA_PATH = "./client-data/bench/" + self.s['obstaclesType'] + "/optimizer-data/"
		print("\nexport_meta_and_client_data ---------------------- ")
		print("exporting obstacles_all")
		with open(self.path_local + 'meta/obstacles_all.json', 'w') as f:  # TODO find out why this is dumped
			json.dump(self._graph_gen.obstacles_all, f, indent=4)

		print("exporting config...")
		with open('./benchmarking/utils_benchmarking/config_template.json', 'r') as f:
			config = json.load(f)
		config['ID'] = self.s['obstaclesType']
		with open(self.CLIENT_DATA_PATH + 'config.json', 'w') as f:
			json.dump(config, f, indent=4)

		print("exporting allcoords...")
		# if self.s['requestType'] == "storageassignment":  # without these one needs to find out where obstacles "start"
		with open(self.path_local + 'meta/allcoords_no_obstacles', 'wb') as f:
			pickle.dump(self._graph_gen.allcoords_no_obstacles, f)

		with open(self.CLIENT_DATA_PATH + 'allcoords', 'wb') as f:
			pickle.dump(self._graph_gen.allcoords, f)

		print("exporting locKeyInd")
		with open(self.CLIENT_DATA_PATH + 'locKeyInd.json', 'w') as f:
			json.dump(self.locKeyInd, f)

		# SET LOCATIONS == allcoords
		self.bo['LOCATION_COORD_SECTION'] = {}
		for i in range(0, len(self._graph_gen.allcoords)):
			self.bo['LOCATION_COORD_SECTION'][str(i)] = self._graph_gen.allcoords[i]

		self.bo['NUM_LOCATIONS'] = len(self._graph_gen.allcoords)

		print("exporting distmat, startendndarray and spnodeslist")
		with open(self.CLIENT_DATA_PATH + 'distmat', 'wb') as f:
			pickle.dump(self._graph_gen.distmat, f)

		with open(self.CLIENT_DATA_PATH + 'startendndarray', 'wb') as f:
			pickle.dump(self._graph_gen.startendndarray, f)

		with open(self.CLIENT_DATA_PATH + 'spnodeslist', 'wb') as f:
			pickle.dump(self._graph_gen.spnodeslist, f)

	def export_required_tsplib_parent_fields(self):

		tsplib_parent = deepcopy(self.bo)

		OBSTACLES = {}  # obstacles_all to OBSTACLED (tsplib)

		with open(self.path_local + 'meta/obstacles_all.json', 'r') as f:
			obstacles_all = json.load(f)

		for i in range(1, len(obstacles_all) + 1):
			OBSTACLES[str(i)] = obstacles_all[str(i)]['inds']
		tsplib_parent['OBSTACLES'] = OBSTACLES

		with open(self.path_local + 'tsplib_parent.json', 'w') as f:
			json.dump(tsplib_parent, f, indent=4, sort_keys=True)

	def export_AB(self):
		"""
		Debug export of Available Boxes
		:return:
		"""
		print("saving files...")
		# dir_output = './benchmarking/BDEV/'
		# dir_output = './benchmarking/files/bench/'

		# with open(dir_output + 'bo_gen0', 'wb') as f:
		# 	pickle.dump(self.bo, f)

		# with open(self.path_local + 'AB', 'wb') as f:
		# 	pickle.dump(self.AB, f)

		with open(self.path_local + 'meta/AB_list', 'wb') as f:
			pickle.dump(self.AB_list, f)

	def build_AB_tsplib_dict(self, export=True):
		"""
		Note tis export
		similar to bodict but this includes a bunch of tsplib bloat (not really needed) i.e. kept separate
		THIS IS SAVED AS A JSON THAT CAN THEN BE USED FOR REPRODUCIBILITY AND CONVERTED TO TSPLIB
		duration section not used
		This function only generates a json.  export_tsplib in OBP_simulator generates the .txt
		"""

		di = deepcopy(self.bo)

		if self.s['requestType'] == "singlebatch" or self.s['requestType'] == "multibatch":
			problem_type = "OBP"
		elif self.s['requestType'] == "storageassignment":
			problem_type = "SLAP"
		else:
			raise Exception("FAAAA")

		di["HEADER"] = {"VERSION": "VRPTEST 1.0",
						"COMMENTS": {"descr": "Modified tsplib for the " + problem_type,
									 "Best known objective": "",
									 "Computational time (s)": ""}
						}
		di["NAME"] = self._tsplib_name
		# di["NUM_DEPOTS"] = self.bo['NUM_DEPOTS']
		di["NUM_CAPACITIES"] = 1
		di["NUM_VISITS"] = self.bo['NUM_VISITS']
		di["NUM_VEHICLES"] = self.s['numVehicles']
		di["CAPACITIES"] = self.s['mobileUnitCapacities']['numOrders']  # NOT SCALABLE
		di["DATA_SECTION"] = ""
		# di["DEPOTS"] = self.bo['DEPOTS']
		# di["DEPOT_LOCATION_SECTION"] = self.bow["DEPOT_LOCATION_SECTION"]

		# DEMAND_SECTION = {}
		VISIT_LOCATION_SECTION = {}

		# last_visit_loc_i =
		if len(self.obstacles_all) > 1:
			pass

		# SKU NAMES MUST CONSTITUTE A RANGE
		for i in range(len(di["DEPOTS"]), self.num_visits_no_duplicates + len(di["DEPOTS"])):
			# DEMAND_SECTION[str(i)] = "-1"
			assert(str(i) in self.SKUs_all)
			loc = self.SKUs_all[str(i)]['location']
			VISIT_LOCATION_SECTION[str(i)] = loc

		di["VISIT_LOCATION_SECTION"] = VISIT_LOCATION_SECTION

		# # test that above is correct
		# for order_id, order in self.O.items():
		# 	assert(order['pick_locs_in_keydict'] == order['pick_locs'])  # might be removed later if sorting not to be used.
		# 	for pl in order['pick_locs_in_keydict']:
		# 		loc = int(VISIT_LOCATION_SECTION[pl])  # test that pick loc KEY exists
		# 		test_loc = self.bo['LOCATION_COORD_SECTION'][loc]  # test that location exists
		# aa = 6

		# di["DEMAND_SECTION"] = DEMAND_SECTION
		# di["NUM_LOCATIONS"] = len(self.bo['LOCATION_COORD_SECTION'])  # hence num_locations has nothing to do with obstracles, BUT LOCATION_COORD_SECTION does
		# if self.s['requestType'] != 'storageassignment':
		# 	di["NUM_LOCATIONS"] = self.num_visits_no_duplicates + len(di["DEPOTS"]) + len(self.obstacles_all) * 4

		# NOT INCLUDED ANYMORE
		# di["LOCATION_COORD_SECTION"] = {}  # by now obstacles have been added
		# for i in range(0, di["NUM_LOCATIONS"]):  # ube
		# 	x = self.bo['LOCATION_COORD_SECTION'][i][0]
		# 	y = self.bo['LOCATION_COORD_SECTION'][i][1]
		# 	di["LOCATION_COORD_SECTION"][str(i)] = (str(x), str(y))


		di["TIMESTEP"] = "1"

		ORDERS = {}
		TIME_AVAIL_SECTION = {}  # OBS THIS WILL BE DIFFERENT IF ORDER-INTEGRITY NOT REQUIRED
		for i in range(1, len(self.O) + 1):  # assumes orders are numbered starting at 1

			o = self.O[str(i)]
			TIME_AVAIL_SECTION[str(i)] = str(o['available_from'])

			ORDERS[str(i)] = o['orderPickItems']['SKUs']

		di['ORDERS'] = ORDERS
		di['TIME_AVAIL_SECTION'] = TIME_AVAIL_SECTION

		# if self.s['obstaclesType'] == 'None':
		# 	pass
		# else:
		# 	di['OBSTACLES'] = {}
		# 	for obstacle_key in self.obstacles_all:
		# 		di['OBSTACLES'][obstacle_key] = []
		# 		for ind in self.obstacles_all[obstacle_key]['inds']:
		# 			di['OBSTACLES'][obstacle_key].append(str(ind))

		if export == True:
			with open(self.path_local + 'meta/tsplib_di_temp.json', 'w') as f:  # not saved as json here since it's just temp anyway
				json.dump(di, f, indent=4, sort_keys=True)

		return di

	def visualize_coords(self, export=False):

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
		for rect_coords in self._graph_gen.OBSTACLESANDDUMMYOBSTACLES:
			xs_rect = [k[0] for k in rect_coords]
			ys_rect = [k[1] for k in rect_coords]
			ax.plot(xs_rect, ys_rect, '-', markersize=4, color='red')
			for tuple in rect_coords:
				xs.append(tuple[0])
				ys.append(tuple[1])
		ax.plot(xs, ys, '+', markersize=8, color='red')

		# PICK LOCS
		xs = []
		ys = []
		for tuple in self._graph_gen.allcoords_no_obstacles:
			xs.append(tuple[0])
			ys.append(tuple[1])

		ax.plot(xs, ys, 'x', markersize=6, color='black')

		for i in range(0, len(self.s['depotSection'])):
			ax.plot(xs[i], ys[i], 's', markersize=15, color='blue')

		if export == True:
			fig.savefig(self.path_local + 'picture_warehouse.png')
		else:
			plt.show()

# with open('./bo_files/bo_c75D', 'rb') as f:
# 	bodict = pickle.load(f)

#

if __name__ == "__main__":

	with open("./benchmarking/tsplibfiles/1_1v4/NoObstaclesL/meta/s_gen_NoObstaclesL.json", "r") as f:
		specs = json.load(f)
	# OBSOBSOBS FIX SO config.json is generated. It is currently not deleted
	bog = Generator(specs, EXPORT_PATH_OUTER=None)  # HHEEE
	bog.run(digit_type='digitize_warehouse', just_visualize=False)

	# with open('./client-data/bench/Conventional/optimizer-data/allcoords', 'rb') as f:
	# 	allcoords = pickle.load(f)
	# temp
	aa = 5

