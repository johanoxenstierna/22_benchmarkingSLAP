"""
# Figliozzi 2008 (for CVRP and some with time-windows)
# dist = b * ((n - m) / n) * sqrt(A * n) + m * 2 * r
# r: average distance between customers and depot
# b: constant to tune
# n: number of customers
# m: number of sought routes (always 1 for tsp)
"""
import os
import numpy as np
import json
import random
import pickle

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib.patches as mpatches

from _8_res_analysis_OBP import compute_std, compute_area

col0 = 'blue'
col1 = 'black'
col2 = 'green'
col3 = 'purple'
col4 = 'red'

def preprocess(PATH, type_of_path):

	from sklearn.model_selection import train_test_split

	X = []
	y = []

	if type_of_path == 'one':
		# 1. find files
		_, folders, _ = os.walk(PATH).__next__()  # name, folders, files

		for folder_name in folders:
			with open(PATH + folder_name + "/" + folder_name + ".json", 'r') as f:
				_d = json.load(f)  # In python, the json is converted to a dictionary . _d is the result

			num_pick_locs_in_SB = float(_d['NUM_LOCATIONS'])
			dist = float(_d['HEADER']['COMMENTS']['Best known objective'])
			# std_xy = compute_std(_d)
			# std_xy_mean = (std_xy[0] + std_xy[1]) // 2
			# area = compute_area(_d)
			comp_time = float(_d['HEADER']['COMMENTS']['Computational time (s)'])
			# X.append([num_pick_locs_in_SB, std_xy[0], std_xy[1], area, std_xy_mean])
			X.append([num_pick_locs_in_SB, comp_time])
			y.append(dist)

	elif type_of_path == 'all':
		# ALLOWED_SUB_PATHS = ['2s/', '2s_1o/', '2s_12o/', '2s_12o_d/', '40v/', '120v/']
		num_instances = 0
		ALLOWED_SUB_PATHS = ['2s/', '2s_1o/', '2s_12o/', '2s_12o_d/', '40v/']  #, '120v/']

		for SUB_PATH in ALLOWED_SUB_PATHS:
			_, folders, _ = os.walk(PATH + SUB_PATH).__next__()  # name, folders, files
			num_instances += len(folders)
			for folder_name in folders:
				with open(PATH + SUB_PATH + folder_name + "/" + folder_name + ".json", 'r') as f:
					_d = json.load(f)  # In python, the json is converted to a dictionary . _d is the result

				num_pick_locs = float(_d['NUM_LOCATIONS'])
				dist = float(_d['HEADER']['COMMENTS']['Best known objective'])
				std_xy = compute_std(_d)
				std_xy_mean = (std_xy[0] + std_xy[1]) // 2
				area = compute_area(_d)
				comp_time = float(_d['HEADER']['COMMENTS']['Computational time (s)'])

				# try:
				# 	X.extend([num_pick_locs_in_SB, std_xy[0], std_xy[1], area, std_xy_mean])
				# 	y.extend(dist)
				# except:
				X.append([num_pick_locs, std_xy[0], std_xy[1], area, std_xy_mean, comp_time])
				y.append(dist)

		print("num_instances: " + str(num_instances))

	X = np.asarray(X)
	y = np.asarray(y)

	# X = np.array([[0.4, 0.1], [0.6, 0.1], [0.8, 0.6], [0.9, 0.4]])
	# y = np.array([0.5, 0.7, 0.9, 1.1])
	X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

	return X, y, X_train, X_test, y_train, y_test


def christofides_dist(n, A, c):
	"""
	Christofides 1969
	Probably useless but could try to tune c
	"""
	dist = c * np.sqrt(n * A)
	return dist


def build_decision_tree(X_train, y_train):
	from sklearn import tree

	# dt = tree.DecisionTreeRegressor()
	# dt = dt.fit(X_train, y_train)
	# PATH_TO_SAVE =
	# with open("./benchmarking/tsplibfiles/0_tsp/models/my_dt", 'wb') as f:
	# 	pickle.dump(dt, f)

	# JUST LOAD
	with open("./benchmarking/tsplibfiles/0_tsp/models/dt_all", 'rb') as f:
		dt = pickle.load(f)

	return dt


def MAPE(targets, predictions):
	return np.mean(np.abs((targets - predictions) / targets))


def generate_linspaces(X, num_x, num_y):

	Xn = np.linspace(min(X[:, 0]), max(X[:, 0]), num_x, dtype=float)  # num_pick_locs
	Yn = np.linspace(min(X[:, -1]), max(X[:, -1]), num_y, dtype=float)  # std

	return Xn, Yn


def dt_test_set_pred(dt, X_test, y_test):

	preds = dt.predict(X_test[:, 0:-1])
	_MAPE = MAPE(y_test, preds)
	print("MAPE: " + str(_MAPE))
	return dt


def dt_predictions_for_visuals(dt, X, X_axis, Y_axis):
	"""
	Y_axis is the mean between x_std and y_std, which is not present so needs to be created first
	"""

	preds = np.zeros((len(X_axis), len(Y_axis)))


	# # USED TO FILL IN MISSING VALUES
	# num_pl_mean = float(int(np.mean(X_test[:, 0])))
	std_x_mean = np.mean(X_test[:, 1])
	std_y_mean = np.mean(X_test[:, 2])
	area_mean = np.mean(X_test[:, 3])
	# single_sample = np.asarray([4, std_x_mean, std_y_mean, 5])
	# sparse_prediction = dt.predict(single_sample.reshape(1, -1))[0]

	single_pred = np.zeros((1, 4))

	for i_xa in range(len(X_axis)):
		for j_ya in range(len(Y_axis)):
			single_pred[0, 0] = X_axis[i_xa]
			single_pred[0, 1] = Y_axis[j_ya]  # std_x
			single_pred[0, 2] = Y_axis[j_ya]  # std_y
			single_pred[0, 3] = area_mean
			preds[i_xa, j_ya] = dt.predict(single_pred)

	# predictions = dt.predict(X)
	# predictions = np.reshape(predictions, (21, 1))
	# # _MAPE = MAPE(y_test, predictions)
	# # print(_MAPE)
	return preds


def plot_controller(X, Y, Z):


	fig = plt.figure(figsize=(10, 7))
	ax = Axes3D(fig)

	ax = plot_predictor(ax, X, Y, Z)
	# ax = plot_data(ax)

	ax.set_xlabel("number_of_items_in_batch")  #
	ax.set_ylabel("standard deviation of vertices")  #
	ax.set_zlabel("optimal_distance")  #

	ax.text2D(0.15, 0.95, "TSP distance prediction data and model", transform=ax.transAxes)

	col1_patch = mpatches.Patch(color='blue', label='Prediction model')
	# r1 = mpatches.Patch(color=col1, label='d1: No obstacles')
	# r2 = mpatches.Patch(color=col1, label='d2: 1 obstacle')
	# r3 = mpatches.Patch(color=col1, label='d3: 2 obstacles')
	# r4 = mpatches.Patch(color=col1, label='d4: 2 obstacles and DARP')
	# r5 = mpatches.Patch(color=col1, label='d5: Fixed number of vertices')
	# fig.legend(handles=[col1_patch, r1, r2, r3, r4, r5], loc='upper right', bbox_to_anchor=(0.5, 0.5, 0.5, 0.5))

	r1 = mpatches.Patch(color=col1, label='prediction points')
	fig.legend(handles=[col1_patch, r1], loc='upper right', bbox_to_anchor=(0.5, 0.5, 0.5, 0.5))  # for pic export

	# for angle in range(0, 1280):  # 1280
	# 	ax.view_init(15, angle)
	# 	plt.pause(.001)
	# 	plt.draw()

	plt.show()


def plot_predictor(ax, X, Y, Z):

	Xm, Ym = np.meshgrid(X, Y)
	ax.plot_surface(Xm, Ym, Z, rstride=1, cstride=1, alpha=0.3, label='DT')  #, cmap='hot')

	return ax


def plot_data(ax):
	PATH_results = "./benchmarking/tsplibfiles/0_tsp/results/"
	r1 = np.load(PATH_results + 'result_2s.npy')
	r2 = np.load(PATH_results + 'result_2s_1o.npy')
	r3 = np.load(PATH_results + 'result_2s_12o.npy')
	r4 = np.load(PATH_results + 'result_2s_12o_d.npy')
	r5 = np.load(PATH_results + 'result_40v.npy')
	r6 = np.load(PATH_results + 'result_120v.npy')

	ax.scatter(r1[:, 0], r1[:, 1], r1[:, 3], c=col4, marker='.', linewidths=1)  # OBS AREA
	ax.scatter(r2[:, 0], r2[:, 1], r2[:, 3], c=col4, marker='.', linewidths=1)
	ax.scatter(r3[:, 0], r3[:, 1], r3[:, 3], c=col4, marker='.', linewidths=1)
	ax.scatter(r4[:, 0], r4[:, 1], r4[:, 3], c=col4, marker='.', linewidths=1)
	ax.scatter(r5[:, 0], r5[:, 1], r5[:, 3], c=col4, marker='.', linewidths=1)
	ax.scatter(r6[:, 0], r6[:, 1], r6[:, 3], c=col4, marker='.', linewidths=1)

	return ax


def plot_comp_time(X):
	fig = plt.figure(figsize=(10, 7))
	ax = plt.scatter(X[:, 0], X[:, -1])

	plt.xlim([0, 250])
	plt.ylim([0, 3])

	plt.xlabel("number_of_items_in_batch")  #
	plt.ylabel("computational_time (s)")  #
	plt.show()


# PATH = "./benchmarking/tsplibfiles/0_tsp/1s_3CAo/"
# PATH = "./benchmarking/tsplibfiles/0_tsp/"
# PATH = "./benchmarking/tsplibfiles/1_1v/2s_NS2o/"
PATH = "./benchmarking/tsplibfiles/2_dyn2/"

X, y, X_train, X_test, y_train, y_test = preprocess(PATH, type_of_path='one')  # or 'one'


# COMP TIME ---------------
num_picks_me = np.mean(X[:, 0])
dist_me = np.mean(y)
dist_per_pick_me = np.mean(y) / num_picks_me
comp_time_me = np.mean(X[:, -1])
comp_time_md = np.median(X[:, -1])

gg = 5

# plot_comp_time(X)

# # DT ------------------
# dt = build_decision_tree(X_train[:, 0:-2], y_train)  # don't train on xy_stds or computational time
# dt = dt_test_set_pred(dt, X_test, y_test)
#
# # VISUALIZATION
# X_axis, Y_axis = generate_linspaces(X, 30, 30)
# Z_n = dt_predictions_for_visuals(dt, X, X_axis, Y_axis)  # predicitons. HAS TO BE IN 2D
#
# plot_controller(X_axis, Y_axis, Z_n)


hg = 56


