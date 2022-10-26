"""MIGHT NOT BE USED (USE RANDOM SEED INSTEAD)"""

import pickle

class TSPLIB_repr:

	def __init__(self, old_tsplib, temp):
		self.TSPLIBtemp = temp

		with open('./benchmarking/BDEV_May_2020/AB', 'rb') as f:
			self.ABtemp = pickle.load(f)

		with open('./benchmarking/BDEV_May_2020/AB_all', 'rb') as f:
			self.AB_alltemp = pickle.load(f)

		with open('./client-data/bench/optimizer-data/allcoords', 'rb') as f:
			self.allcoords_temp = pickle.load(f)

		with open('./client-data/bench/optimizer-data/distmat', 'rb') as f:
			self.distmat_temp = pickle.load(f)

		with open('./client-data/bench/optimizer-data/keydict', 'rb') as f:
			self.keydict_temp = pickle.load(f)

		with open('./client-data/bench/optimizer-data/spnodeslist', 'rb') as f:
			self.spnodeslist_temp = pickle.load(f)

		with open('./client-data/bench/optimizer-data/startendndarray', 'rb') as f:
			self.startendndarray_temp = pickle.load(f)


		self.depots()
		self.boxes()
		self.boxes_available_from()
		self.init_obstacles()
		self.coordinates()

	def depots(self):
		aa = 6