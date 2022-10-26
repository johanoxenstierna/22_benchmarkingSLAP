
import time
import json
import os
"""
Does not have visualizations, so is a bit simpler than original
"""

class TSPLIBexporterSLAP:

	def __init__(self, specs, EXPORT_PATH_OUTER, _g, req, res):
		"""
		_g: generator instance
		"""
		self.FLAG_FIRST_RUN = True
		self.NAME_OPTIMIZER = 'SBI-QAS'

		self.req = req
		self.res = res

		# self.b_log = res['benchmark_log']
		# self.best_particle = res['best_particle']
		self._g = _g
		self.di = _g.di
		self.EXPORT_PATH_INNER = EXPORT_PATH_OUTER + _g.s['obstaclesType'] + "/instances/"
		self.EXPORT_PATH_INNER_INNER = self.EXPORT_PATH_INNER + self.di['NAME'] + '/'

		aa = 5

	def export_tsplib_jsons(self):
		"""
		SAME FUNCTION AS IN THE ORIGINAL EXPORTER CLASS
		Exports 1. tsplib as json (for easier use later), 2. tsplib as txt
		3. save self.sol_jsons
		Does not store results of individual QuickBatch calls (do separate investigation session)
		"""
		best_particle = self.res['best_particle']

		# TSPLIB JSON EXPORT --------------------------------------------
		self.di['HEADER']['COMMENTS']['descr'] = "Modified TSPLIB for the SLAP"
		self.di['HEADER']['COMMENTS']["Best known objective"] = str(round(best_particle['OBP_res'], 3))  # converted to dm (should still be float)
		self.di['HEADER']['COMMENTS']["Computational time (s)"] = str(self.res['time_tot'])  # converted to dm (should still be float)
		self.di['HEADER']['VERSION'] = 'SLAP 1.0'
		self.di['SKUS_TO_SLOT'] = [x for x in self.req['requestData']['SKUsToSlot'].keys()]

		self.req['requestData']['SKUsToSlot'].keys()
		self.di['ASSIGNMENT_OPTIONS'] = self.req['requestData']['assignmentOptions']

		print("saving " + str(self.di['NAME']))
		if self.FLAG_FIRST_RUN == True:  # i.e. it hasn't been created yet
			os.mkdir(self.EXPORT_PATH_INNER + self.di['NAME'])

		# self.EXPORT_PATH_OUTER = self.EXPORT_PATH_OUTER + name + "/"

		# PATH_SOL = self.EXPORT_PATH_INNER + self.sol_jsons['optimizerUsed'] + "/"

		# SAVE TSPLIB JSON ====================
		# if self.s['requestType'] != 'storageAssignment':

		# if self.flag_first_run == False:
		# 	self.validate_update_jsons_OBP()

		time0 = time.time()
		with open(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '.json', 'w') as f:  # with line breaks etc.
			json.dump(self.di, f, indent=4, sort_keys=True)  # indent=4

		# SAVE SOLUTION --------------------------------------
		# self.sol_jsons['solutionDistance'] = self.result_distance * 10
		# self.sol_jsons['computationalTime(s)'] = total_comp_time

		print("time to save self.di: " + str(time.time() - time0))

		# # SAVE SPECS ===========================
		# self._g.s['nameTsplib'] = self.di['NAME']
		with open(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '_specs.json', 'w') as f:
			json.dump(self._g.s, f, indent=4)  # , sort_keys=True)
		#
		# time0 = time.time()
		# print("time to save plot_res: " + str(time.time() - time0))
		# print("\n")

	def export_solution(self):

		SKUs_and_inds = {}
		for key, val in self.res['best_particle']['SKUs_all'].items():\
			SKUs_and_inds[key] = val['ind_current']
		with open(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '_sol.json', 'w') as f:
			json.dump(SKUs_and_inds, f, indent=4)  # , sort_keys=True)

	def export_QAP_accuracy_result(self):

		with open(self.EXPORT_PATH_INNER_INNER + self.di['NAME'] + '_QAPlog.json', 'w') as f:
			json.dump(self.res['benchmark_log'], f, indent=4)  # , sort_keys=True)




