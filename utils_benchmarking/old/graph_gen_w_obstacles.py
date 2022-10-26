"""
MODULE USED IN _2_GENERATOR WHEN OBSTACLES ARE NEEDED
PROB DEPR
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import LineString, Point, Polygon
import networkx as nx
import pickle
import json
from benchmarking.utils_benchmarking.auto_gen_obst_types import *


class GraphGen:
	"""
	Uses the functions in auto_gen_obst_types.py
	Obstacles have to be significantly smaller than the slots.
	"""

	def __init__(self, s):
		self.s = s  # specs
		self.allcoords = None  # inited later
		self.allcoords_no_obstacles = None
		self.distmat = None
		self.SPNODEPATHS = None

	def define_obstacles(self, obstaclesType, possibleVisitLocs, DEBUGGING):
		"""
		allcoords are created by the generator class.
		:return:
		"""

		if obstaclesType == 'NoObstacles' or obstaclesType == 'NoObstaclesL':  #
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords = empty_placeholders(possibleVisitLocs)
		elif obstaclesType == 'SingleRack':
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords = SingleRack(possibleVisitLocs)
		elif obstaclesType == 'TwelveRacks':
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords = TwelveRacks(possibleVisitLocs)
		elif obstaclesType == 'Conventional':
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords = Conventional(DEBUGGING)
		elif obstaclesType == 'NR1':
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords = NR1()  # allowed_coords is allowed pick locations
		elif obstaclesType == 'NR2':
			self.obstacles_all, self.forbidden_regs, self.allowed_regs, self.allowed_coords  = NR2()

	def gen_OBSTACLESANDDUMMYOBSTACLES(self):
		"""
		This shoudl be  deprecated in real warehouse digitization repo: The OBSTACLESANDDUMMYOBSTACLES is replaced by
		different dicts.
		"""
		self.OBSTACLESANDDUMMYOBSTACLES = []  # list_of_obstacles coorner coordinates

		for key_obs in self.obstacles_all:
			obs_corners = self.obstacles_all[key_obs]['corners']
			self.OBSTACLESANDDUMMYOBSTACLES.append(obs_corners)

	def run_graph_build(self):
		"""
		allcoords inited before this func.
		DEPRECATED AS OF FEB 2021
		:return:
		"""

		# OBS! DUMMIES: 401, 924, boundaries
		REALOBJECTCORNERINDICIES = []  # obstacles_inds_list
		for rack_id in self.obstacles_all:  # gen obstacles_inds_list
			# if rack_id != '401' and rack_id != '924' and rack_id[0:2] != 'd_':
			# rack = obstacles_all[rack_id]
			REALOBJECTCORNERINDICIES.append(self.obstacles_all[rack_id]['inds'])
		self.REALOBJECTCORNERINDICIES = REALOBJECTCORNERINDICIES

		ADJMAT, polylist = self.generateADJMAT()  # 10 min for ~1500 nodes
		# self.visualizeAdjMat(ADJMAT, polylist)  # 1 min for 500 nodes, 1 hour for ~3500 nodes
		WADJMAT = self.generateWeightedADJMAT(ADJMAT)
		self.distmat, SPNODEPATHS = self.generateGraphNetwork(ADJMAT, WADJMAT)
		self.spnodeslist, self.startendndarray = self.split_SPNODESPATH(SPNODEPATHS)

	def generateADJMAT(self):

		'''
		# Polygons must follow clockwise coordinate convention
		:param OBSTACLESANDDUMMYOBSTACLES:
		:param ALLNODES:
		:param REALOBJECTCORNERINDICIES:
		:return:
		'''

		polylist = []  # to store shapely polygon objects

		for obstacle in self.OBSTACLESANDDUMMYOBSTACLES:  # convert obstacle polygons to shapely polygon objects
			polylist.append(Polygon(obstacle))

		print('Generating ADJMAT')
		matty = np.ndarray((len(self.allcoords), len(self.allcoords)), dtype=bool)

		# Initialize adjacency matrix as fully connected
		for i in range(0, len(self.allcoords) - 1):
			for j in range(i, len(self.allcoords)):
				matty[i, j] = 1
				matty[j, i] = 1

		# Deny edges in adjacency matrix that are obstructed
		print('Pruning Obstructed Edges')
		for i in range(0, len(self.allcoords) - 1):
			print('Edges for Node ', i, 'of ', len(self.allcoords), ' nodes.')
			for j in range(i + 1, len(self.allcoords)):
				for poly in polylist:
					shapely_line = LineString([tuple(self.allcoords[i]), tuple(self.allcoords[j])])
					if poly.intersection(shapely_line).length != 0:  # condition where line is obstructed
						matty[i, j] = 0
						matty[j, i] = 0
						break  # break out of polygon loop, no need to check others as we know these points i and j are obstructed.

		ADJMAT = matty
		ADJMAT = self.connectPolygonEdges(ADJMAT)
		# with open('ADJMAT', 'wb') as handle:
		# 	pickle.dump(ADJMAT, handle, protocol=pickle.HIGHEST_PROTOCOL)

		# print('Visualizing...')
		# # if visualize:  # set to 1 to plot edges and obstacles
		# matplotlib.rcParams['agg.path.chunksize'] = 10000
		#
		# # % matplotlib
		# # inline
		# plt.rcParams['figure.figsize'] = (8.0, 6.0)
		#
		# fig, ax = plt.subplots()
		# plt.title('Connected Edges Around Obstacles, Inspect for Mapping Errors')
		# # polygon_shape = patches.Polygon(points, linewidth=1, edgecolor='r', facecolor='none')
		# # ax.add_patch(polygon_shape)
		# for i in range(0, len(polylist)):
		# 	x, y = polylist[i].exterior.coords.xy
		# 	points = np.array([x, y], np.int32).T
		#
		# 	# fig, ax = plt.subplots(1)
		# 	polygon_shape = patches.Polygon(points, linewidth=1, edgecolor='r', facecolor='none')
		# 	ax.add_patch(polygon_shape)
		# plt.axis("auto")
		#
		# print('Visualizing...')
		# for i in range(0, len(ALLNODES) - 1):
		# 	for j in range(i + 1, len(ALLNODES)):
		# 		if matty[i, j] == True:
		# 			ax.plot([ALLNODES[i][0], ALLNODES[j][0]], [ALLNODES[i][1], ALLNODES[j][1]], color='b', lw=.25)
		# plt.show()
		# print('ADJMAT Generated.')

		return ADJMAT, polylist

	def connectPolygonEdges(self, ADJMAT):
		"""
		OBS the only difference between this and the one in digit module is that this one assumes
		that all locations are accessible.
		:param ADJMAT:
		:param REALOBJECTCORNERINDICIES:
		:return:
		"""
		for objectIdList in self.REALOBJECTCORNERINDICIES:
			for i in range(0, len(objectIdList) - 1):
				ADJMAT[objectIdList[i], objectIdList[i + 1]] = 1
				ADJMAT[objectIdList[i + 1], objectIdList[i]] = 1
			# Connect last to first
			ADJMAT[objectIdList[0], objectIdList[len(objectIdList) - 1]] = 1
			ADJMAT[objectIdList[len(objectIdList) - 1], objectIdList[0]] = 1

		return ADJMAT

	def generateWeightedADJMAT(self, ADJMAT):
		'''
		Get distances for reachable pairs of nodes. simply euclidean given there are no obstructions
		:param ALLNODES:
		:param ADJMAT:
		:return:
		'''

		distMatrix = np.ndarray(shape=(len(self.allcoords), len(self.allcoords)), dtype=np.float16)  # zeros?
		print('Generating WADJMAT')
		for i in range(0, len(self.allcoords) - 1):
			for j in range(i + 1, len(self.allcoords)):
				if ADJMAT[i, j] == 1:
					# calculate distance
					distMatrix[i, j] = np.sqrt((self.allcoords[i][0] - self.allcoords[j][0]) ** 2 + (
						self.allcoords[i][1] - self.allcoords[j][1]) ** 2)  # euclidean dist)
					distMatrix[j, i] = distMatrix[i, j]
				else:
					distMatrix[i, j] = 0
					distMatrix[j, i] = distMatrix[i, j]

		for i in range(0, len(self.allcoords)):
			distMatrix[i, i] = 0

		# commented out cuz distances are INT (for some f* reason)
		# # run check to make sure no zero rounding has occured:
		# for i in range(0, len(self.allcoords) - 1):
		# 	for j in range(i + 1, len(self.allcoords)):
		# 		if ADJMAT[i, j] == 1:
		# 			assert (distMatrix[i, j] > 0)
		# print'All int valued distances in WADJMAT are greater than 0'

		WADJMAT = distMatrix
		print('done Generating WADJMAT')

		return WADJMAT

	def generateGraphNetwork(self, ADJMAT, WADJMAT):

		'''
		# generate Graph in networkx
		:param ADJMAT:
		:param WADJMAT:
		:param ALLNODES:
		:return:
		'''

		print('generateGraphNetwork')
		rows, cols = np.where(ADJMAT == 1)
		dists = WADJMAT[rows, cols]
		edges = zip(rows.tolist(), cols.tolist(), dists.tolist())
		gr = nx.Graph()
		print("done nx.Graph")
		gr.add_weighted_edges_from(edges)

		# generate shortest path routes

		SP = nx.shortest_path(gr, weight='weight')
		print("done nx.shortest_path")
		# with open('SPNODEPATHS', 'wb') as handle:
		# 	pickle.dump(SP, handle, protocol=pickle.HIGHEST_PROTOCOL)

		SPDistMatrix = np.ndarray(shape=(len(self.allcoords), len(self.allcoords)), dtype=np.float16)

		for i in range(0, len(self.allcoords)):  # - 1):
			for j in range(i, len(self.allcoords)):  # i + 1, len(ALLNODES)):
				if i == j:
					SPDistMatrix[i, j] = 0
					SPDistMatrix[j, i] = 0
				else:
					distanceForThisPair = 0
					sequenceOfTransitions = SP[i][j]
					for k in range(0, len(sequenceOfTransitions) - 1):
						distanceForThisPair = distanceForThisPair + (np.sqrt((self.allcoords[sequenceOfTransitions[k]][0] - self.allcoords[sequenceOfTransitions[k + 1]][0]) ** 2 + (
							self.allcoords[sequenceOfTransitions[k]][1] - self.allcoords[sequenceOfTransitions[k + 1]][1]) ** 2))
					SPDistMatrix[i, j] = distanceForThisPair
					SPDistMatrix[j, i] = distanceForThisPair

			if i % 10 == 1:
				print(i)

		# with open('SPDISTMAT', 'wb') as handle:
		# 	pickle.dump(SPDistMatrix, handle, protocol=pickle.HIGHEST_PROTOCOL)
		print('done generateGraphNetwork')

		return SPDistMatrix, SP

	def visualizeAdjMat(self, ADJMAT, polylist):
		'''
		Visualizes graph result
		:param ADJMAT:
		:param polylist:
		:param ALLNODES:
		:return:
		'''

		print('Visualizing...')
		# if visualize:  # set to 1 to plot edges and obstacles
		matplotlib.rcParams['agg.path.chunksize'] = 10000

		# % matplotlib
		# inline
		plt.rcParams['figure.figsize'] = (3.0, 4.0)

		fig, ax = plt.subplots()
		plt.title('Connected Edges Around Obstacles, Inspect for Mapping Errors')
		# polygon_shape = patches.Polygon(points, linewidth=1, edgecolor='r', facecolor='none')
		# ax.add_patch(polygon_shape)
		for i in range(0, len(polylist)):
			x, y = polylist[i].exterior.coords.xy
			points = np.array([x, y], np.int32).T

			# fig, ax = plt.subplots(1)
			polygon_shape = patches.Polygon(points, linewidth=1, edgecolor='r', facecolor='none')
			ax.add_patch(polygon_shape)
		plt.axis("auto")

		print('Visualizing...')
		for i in range(0, len(self.allcoords) - 1):
			for j in range(i + 1, len(self.allcoords)):
				if ADJMAT[i, j] == True:
					ax.plot([self.allcoords[i][0], self.allcoords[j][0]], [self.allcoords[i][1], self.allcoords[j][1]], color='b', lw=.25)
			if i % 100 == 0:
				print(str(i) + " out of " + str(len(self.allcoords)) + " nodes done")
		plt.show()

		print('ADJMAT Generated.')

	def split_SPNODESPATH(self, SPNODEPATHS):

		# OBS OBS OBS: startend is upper bound exclusive when read.
		startend = np.ndarray([len(self.allcoords), len(self.allcoords), 2], dtype=np.uint32)

		listo = []
		for i in range(0, len(self.allcoords)):
			for j in range(0, len(self.allcoords)):
				if j == 319:
					ggg = 5
				startpos = len(listo)
				listo += SPNODEPATHS[i][j]
				endpos = len(listo)
				startend[i, j, 0] = startpos
				startend[i, j, 1] = endpos
			print(i)

		spnodeslist = np.asarray(listo).flatten().astype(np.int16)

		# startend = startend.reshape(startend.shape[0] * startend.shape[1], 2)  # NEEEEW

		# with open(folder_name + 'startendndarray', 'wb') as handle:
		# 	pickle.dump(startend, handle)  # , protocol=2)
		#
		# with open(folder_name + 'spnodeslist', 'wb') as handle:
		# 	pickle.dump(listo, handle)  # , protocol=2)

		return spnodeslist, startend

# REMEMBER TO DELETE OLD FILES THAT WILL NEVER BE USED