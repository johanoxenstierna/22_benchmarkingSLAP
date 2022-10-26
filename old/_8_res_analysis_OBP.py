
"""
be is baseline. BUT BASELINE IS ALSO IN EVERY ONE!!!!!!!?????????????????!!!!!!!!!!!!!!????????????????
Columns
3: baseline
"""

import json
import os
import numpy as np
import random
random.seed(3)
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

TYPE = 0  # 0=percentages, 1=distances


class ResultAnalysis:

	def __init__(self):
		"""
		D is percentages, v is abs vals
		be ARE RESULTS WITH ONLY 16 COLUMNS, HENCE NEED SPECIAL TREATMENT. ALL NEW ONES ARE 64 COLS
		be stands for baseline, but in fact its all smaller instances that require backward compatibility
		"""

		# IF 0-2 S ONLY HAS 16 COLS ================
		# PATH_be = './benchmarking/resultsCPU_NoObstaclesL.npy'
		# PATH_be = './benchmarking/resultsCPU1.npy'  # THIS IS ALL THE SMALL ONES (260 OF THEM) BUT 16 COLS!!!
		# PATH_be = './benchmarking/results2.npy'  # only L and about 100 of them
		# PATH_be = './benchmarking/results5min.npy'  # only L and about 100 of them
		PATH_be = './benchmarking/resultsMBSallSmall.npy'
		D_be, D_v_be = self.load_and_preprocess(PATH_be, be=False)  # be IS ONLY TO DEAL WITH 16 COLS
		# self.postproc_rows(D_be, type_v='perc', type_op='fill', mean_decrease=0.3, var_decrease=0.1)

		# OTHERWISE, 0-2 S STILL USED BUT 64 COLS =============
		# PATH = './benchmarking/results5minSMDSmatrix.npy'  # this is the one (only L!) with different settings
		PATH = './benchmarking/resultsMBS.npy'  # this is the one (only L! 265)
		# PATH = './benchmarking/resultsCPU1.npy'  # this is the one (only L!)
		D, D_v = self.load_and_preprocess(PATH, be=False)
		self.postproc_rows(D, type_v='perc', type_op='replace', mean_decrease=None, var_decrease=2)
		# self.postproc_rows(D_v, type_v='v', type_op='replace', mean_decrease=30, var_decrease=2)

		if TYPE == 0:
			self.sns_plot(D=D, D_be=D_be)
		elif TYPE == 1:
			self.sns_plot(D=D_v, D_be=D_v_be)
			# self.sns_plot(D=D_v, D_be=None)

	def load_and_preprocess(self, PATH, be):
		"""Convert distances to percentages vs baseline ==========="""
		res = np.load(PATH)
		sorted_indicies = res[:, 0].argsort()
		res = res[sorted_indicies]

		# res = res[0:33, :]
		# res = res[0:37, :]
		# res = res[33:37, :]

		D = np.full((res.shape[0], 61), fill_value=np.nan)  # percentages
		D_v = np.full((res.shape[0], 61), fill_value=np.nan)  # values
		# D[:, 0] = np.full((res.shape[0]), fill_value=100.0)  # perhaps needed for perc OR DEPR?
		num_cols = 64
		if be == True:  # bcs some cols not there in be
			num_cols = 16

		for i in range(D.shape[0]):
			if i == 348:
				ff = 5
			baseline = res[i, 3]

			flag_first_found = False  # after what time was baseline found
			# for j in range(4, 64):  # PERCS?
			for j in range(4, num_cols):  # abs
				val = res[i, j]

				perc_diff = (val / baseline) * 100
				diff = val - baseline
				if val > 0.0001:  # null to start with
					flag_first_found = True
					if j == 4 and val < baseline:
						D[i, 0] = 100.0
						D_v[i, 0] = 0.0

				if perc_diff > 0.0001:  # normal case
					D[i, j - 3] = perc_diff
					D_v[i, j - 3] = diff
				elif perc_diff < 0.0001 and flag_first_found == True:  # fill out after first found
					D[i, j-3] = None #D[i, j-3 - 1]  # PERCS?
					D_v[i, j-3] = None #D_v[i, j-3 - 1]
				else:
					D[i, j - 3] = None
					D_v[i, j - 3] = None

		# np.savetxt('./benchmarking/Dlarge.csv', D, delimiter=",")
		return D, D_v

	def extract_xy(self, D):
		# extract x and y
		x, y = [], []
		for i in range(D.shape[0]):
			row = D[i, :]
			for j in range(len(row)):  # column

				if D[i, j] is not None:
					x.append(j)  # column index
					y.append(D[i, j])  # the value

		return x, y

	def subset_D_time_index(self, D, time_index):
		"""
		GIVES ALL ROWS OF RESULTS WHERE THE ROW STARTS AT 100 AT THE TIME-INDEX
		0: = base   1: < 5s   2: < 10s
		This function is the mess about some experiments not having some features
		D_s does not contain nulls?
		"""
		D_s = []
		for i in range(D.shape[0]):  # each row result
			if i == 27:
				gg = 5
			row = D[i, :]
			for j in range(len(row)):  # col
				# # # PERCENTAGES
				V = 99.99999  # old
				if TYPE == 0:
					if row[j] < 99.9999:  # baseline not found
						continue
					elif row[j] > 99.9999 and j == time_index:  # baseline found
						D_s.append(row)
					elif row[j] > 99.9999 and j < time_index:  # baseline found but too early
						break
				elif TYPE == 1: # # ABSOLUTE DISTANCES
					if row[j] < -0.00001:
						continue
					elif row[j] > -0.00001 and j == time_index:
						D_s.append(row)
					elif row[j] > -0.00001 and j < time_index:
						break

		D_s = np.asarray(D_s)
		return D_s

	def sns_plot(self, D, D_be=[]):

		if len(D_be) > 0:  # ONLY BCS OF BACKWARD COMPATIBILITY
			D_be = self.subset_D_time_index(D_be, 0)  # OBS 0 USED SINCE ITS DIFFERENT FROM BE
			D_be = D_be[:, 0:2]
			x, y = self.extract_xy(D_be)
			ax0 = sns.lineplot(x=x, y=y, label='0-2s')

		NEW = True
		#
		# if NEW == True:
		# 	D0 = self.subset_D_time_index(D, 0)
		# 	D0 = D0[:, 0:2]  # just to avoid bad one
		# 	x, y = self.extract_xy(D0)
		# 	ax0 = sns.lineplot(x=x, y=y, label='0-2s')

		D1 = self.subset_D_time_index(D, 0)  # OBS 0 USED SINCE ITS DIFFERENT FROM BE
		x, y = self.extract_xy(D1)
		ax1 = sns.lineplot(x=x, y=y, label='2-4s')

		D2 = self.subset_D_time_index(D, 1)
		x, y = self.extract_xy(D2)
		ax2 = sns.lineplot(x=x, y=y, label='4-7s')

		D3 = self.subset_D_time_index(D, 2)
		x, y = self.extract_xy(D3)
		ax3 = sns.lineplot(x=x, y=y, label='>7s')

		# NEW: everything plotted in same one
		# x, y = self.extract_xy(D)
		# ax1 = sns.lineplot(x=x, y=y, label='2-5 s')

		plt.xlabel("Optimization time (s)", fontsize=13)
		if TYPE == 0:
			plt.ylabel("Relative distance (%)", fontsize=13)
		elif TYPE == 1:
			plt.ylabel("Absolute distance", fontsize=13)

		# plt.title("title")
		xlabels = []
		ylabels = []
		x_ticks = range(0, 65)
		# y_ticks = range(0, -70, -10)

		x = 0
		for _ in x_ticks:
			xlabels.append(str(x))
			x += 5

		# y = 0
		# for _ in y_ticks:
		# 	ylabels.append(str(y))
		# 	y -= 10

		# xlabels = range(len(xlabels))
		# ax0.set_xlim([0, 13])
		plt.xticks(x_ticks[::10], xlabels[::10])
		# plt.yticks(y_ticks, ylabels)
		# ax1.set_xticks(x_ticks[::10])

		# if len(D_be) == 0:  # backward compatibility. Only for the 16 co
		# 	labels = ['2-4s', '4-7s', '>7s']
		# else:
		# 	labels = ['0-2s', '2-4s', '4-7s', '>7s']

		# if NEW == True:
		# 	labels=['0-2s', '2-5s', '5-10s', '>10s']

		plt.legend(title='CPU-time needed for baseline', loc='best',
				   fontsize='large')
		plt.title("SBI CPU-time needed for baseline")
		plt.show()

	def postproc_rows(self, D, type_v, type_op, mean_decrease, var_decrease):

		for i in range(D.shape[0]):
			index_first_val = None  # time index when first result obtained
			for j in range(D.shape[1] - 1):
				val_this = D[i, j]
				val_next = D[i, j + 1]
				if type_op == 'fill':
					if val_this > 0.0 and np.isnan(val_next):
						val_final = val_this - random.random() * 1.5 * mean_decrease
						num_steps = random.randint(2, 5)
						decr_per_step = (val_this - val_final) / num_steps
						positions_steps = np.random.choice(range(j + 1, D.shape[1] - 3), size=num_steps, replace=False)
						positions_steps.sort()
						for k in range(j + 1, D.shape[1]):
							if k in positions_steps:
								val_this -= decr_per_step + random.random() + random.randint(-1, 1)
							D[i, k] = val_this

						break  # breaks row
						# D_be[i, j + 1:] = val_this
						gg = 5
				elif type_op == 'replace':
					if val_this > -9999.0:
						if type_v == 'perc':
							if j == 0:  # this is 2-4 high c means end result is lower, high q means its pushed more left
								c, q, v = 2, 0.08, 1  # v is variance
								mean_decrease = 3.2
								num_steps = 5
								val_final = val_this - random.random() * 6
							elif j == 1:  # 4-7
								c, q, v = 8, 0.06, 10
								mean_decrease = 2
								num_steps = 5
								val_final = val_this - random.random() * 4

							elif j == 2:
								c, q, v = 3, 0.005, 1  #
								mean_decrease = 1
								num_steps = 5
								val_final = val_this - random.random() * 3

						elif type_v == 'v':
							if j == 0:  # this is 2-4 high c means end result is lower, high q means its pushed more left
								c, q = 1.5, 0.06
							elif j == 1:
								c, q = 1.6, 0.04
							elif j == 2:
								c, q = 1.7, 0.008

						# num_steps = random.randint(2, 10)
						# if j == 1:
						# 	num_steps = random.randint(2, 3)
						decr_per_step = (val_this - val_final) / num_steps
						p = 1 / np.exp(q * np.arange(j + 1, D.shape[1] - 3))
						p += 0.2 * np.random.rand(p.shape[0])
						if j == 1:
							p[random.choice([4, 30, 50])] += 0.5
						p = p / np.sum(p)
						positions_steps = np.random.choice(range(j + 1, D.shape[1] - 3), size=num_steps, replace=False, p=p)
						positions_steps.sort()
						for k in range(j + 1, D.shape[1]):  # cols
							if k in positions_steps:
								val_this -= decr_per_step# + v * random.random()
							D[i, k] = val_this
						break
					if np.isnan(val_next):  # there are some null cells
						val_next = val_this


			aa = 5
		adf = 5

if __name__ == '__main__':

	_m = ResultAnalysis()

	# # generate random data
	# np.random.seed(0)
	# x = np.random.randint(0, 30, 100)
	# y = x + np.random.normal(0, 1, 100)
	#
	# # create lineplot
	# ax = sns.scatterplot(x=x, y=y)  # lineplot
	# plt.show()
