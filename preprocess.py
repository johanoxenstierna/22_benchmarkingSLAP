
"""
This module splits SKUs that have more than one location into multiple SKUs
OBS the data used here is pickrun responses!
"""

import json
import os
from copy import deepcopy
import numpy as np

from EROSKI.SLAP.filter_pros import PickrouteFilter

# PATH_IN = './EROSKI/SLAP/data7_5/'
# PATH_IN = './EROSKI/SLAP/data7_2500/'
PATH_IN = './EROSKI/SLAP/processedData/data7_100f/'
PATH_OUT = './EROSKI/SLAP/processedData/data7_500f/'
FILTER = 0
WRITE = 0

_, folder, files = os.walk(PATH_IN).__next__()
pickingLog = {}
if FILTER:
	_pro_filter = PickrouteFilter()

for i, name in enumerate(files):
	full_path = PATH_IN + name
	with open(full_path, 'r') as f:
		res = json.load(f)
		if FILTER:
			_pro_filter.add_pro(res)
		else:
			pickingLog[i] = res

if FILTER:
	pickingLog = {}
	_pro_filter.filter_on_dist_and_num_skus()
	for i, pro in enumerate(_pro_filter.pros):
		pickingLog[i] = pro


# FILTER COMPLETE =====================================================
count_skus_more_than_one = 0
sku_locs = {}  # filled with skus and locs
locs_skus = {}

for pro_id, pro in pickingLog.items():
	for i, sku in enumerate(pro['requestData']['picksInfo']['SKUs']):
		raw_loc = pro['requestData']['picksInfo']['locations'][i]
		if sku not in sku_locs:
			sku_locs[sku] = {'raw_locs': [raw_loc], 'pros': [pro_id], 'total_occurences': 1}
		else:  # sku is in sku_locs
			# if raw_loc not in sku_locs[sku]['raw_locs']:  # the new raw loc is different from existing one
			sku_locs[sku]['raw_locs'].append(raw_loc)
			# if pro_id not in sku_locs[sku]['pros']:
			sku_locs[sku]['pros'].append(pro_id)
			sku_locs[sku]['total_occurences'] += 1

		if raw_loc not in locs_skus:
			locs_skus[raw_loc] = {'skus': [sku], 'pros': [pro_id]}
		else:
			locs_skus[raw_loc]['pros'].append(pro_id)
			locs_skus[raw_loc]['skus'].append(sku)

# '''The SKUs that need changing'''
skus_new = {}
for sku_id, sku_val in sku_locs.items():
	unique_raw_locs = np.unique(np.array(sku_val['raw_locs']))
	if len(unique_raw_locs) > 1:  # An sku does not have 1 unique location
		'''Bug discovered here. INDEXING MUST START AT 0 EACH TIME'''
		val = {}
		for i, unique_raw_loc in enumerate(unique_raw_locs):
			val[str(unique_raw_loc)] = sku_id + "_" + str(i)
		skus_new[sku_id] = val

		aa = 5

	# if len(sku_val['raw_locs']) > 1:
	# 	val = {}
	# 	for i in range(len(sku_val['raw_locs'])):
	# 		val[sku_val['raw_locs'][i]] = sku_id + "_" + str(i)
	# 	skus_new[sku_id] = val

# aa = sku_locs['3162989']  # 3-87-21  6-155-11
# not_same_len_pros_

'''check num locs vs skus'''

pickingLog_new = deepcopy(pickingLog)

for pro_id, pro in pickingLog_new.items():
	for i in range(len(pro['requestData']['picksInfo']['SKUs'])):
		sku = pro['requestData']['picksInfo']['SKUs'][i]
		raw_loc = pro['requestData']['picksInfo']['locations'][i]  # NEEDED!!! UPDATE
		if sku in skus_new:
			if raw_loc not in skus_new[sku]:
				'''Crucial check. The raw location in the request MUST HAVE BEEN FOUND and put into skus_new'''
				raise Exception("raw loc error")

			sku_new = skus_new[sku][raw_loc]  # 3162989

			'''write it. '''
			pro['requestData']['picksInfo']['SKUs'][i] = sku_new

if WRITE:
	for pro_id, pro in pickingLog_new.items():
		with open(PATH_OUT + str(pro_id) + '.json', 'w') as f:
			json.dump(pro, f, indent=True)

adf = 5