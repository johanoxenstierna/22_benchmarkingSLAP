'''Generate one tag at a time'''

import os
from pathlib import Path
import shutil
import json
import random
random.seed(7)
from copy import deepcopy
from utils_benchmarking.utils import *
from utils_benchmarking import empty_locations

'''instance names int
NR1: 0-
NoObstacles: 100-
TwelveRacks: 200-
Conventional: 300-
SingleRack: 400-
NR2: 500-
'''

# WAREHOUSE_TAG = 'NoObstacles'
# WAREHOUSE_TAG = 'TwelveRacks'
WAREHOUSE_TAG = 'NR1'
NAME_INST_INT_START = 0
PATH0 = './tsplibfiles/1_1v4/' + WAREHOUSE_TAG + '/instances/'
PATH_OUT0 = './tsplibfiles/2_SLAP_PRO/' + WAREHOUSE_TAG + '/'
SAVE = 1

'''Parameters to modify instance'''
# NUM_EMPTY_LOCATIONS = 1
# NUM_DUPLICATE_Os = 0
# NUM_DUPLICATE_SKUs = 0
# NUM_EXTRA_SKUs_IN_PROS = (0, 0) # used to make pickruns longer. Num skus in so many pros

with open('./tsplibfiles/1_1v4/' + WAREHOUSE_TAG + '/tsplib_parent.json', 'r') as f:
    tsplib_parent = json.load(f)

_, inst_names, _ = os.walk(PATH0).__next__()

inst_name_int = NAME_INST_INT_START
for inst_name in inst_names:
    print("generating " + str(inst_name))
    with open(PATH0 + inst_name + '/' + inst_name + '.json', 'r') as f:
        inst_o = json.load(f)

    req_SLAP = init_SLAP_req(WAREHOUSE_TAG, inst_name, inst_name_int,
                             inst_o)

    '''Parameters to modify instance'''
    NUM_EMPTY_LOCATIONS = 0
    NUM_DUPLICATE_Os = 5
    NUM_DUPLICATE_SKUs = 1
    NUM_EXTRA_SKUs_IN_PROS = (10, 2)  # used to make pickruns longer. Num skus in so many pros

    req_SLAP['_meta']['bench']['ALGO'] = None

    # NUM_SKUs = len(instance['VISIT_LOCATION_SECTION'])
    O_keys = list(inst_o['ORDERS'])

    duplicate_orders(inst_o, NUM_DUPLICATE_Os, O_keys)
    add_extra_SKUs(inst_o, NUM_EXTRA_SKUs_IN_PROS,
                   O_keys, tsplib_parent)
    duplicate_SKUs(inst_o, NUM_DUPLICATE_SKUs, O_keys)
    PL = gen_req_PL_and_random_locs(inst_o, inst_name, WAREHOUSE_TAG, tsplib_parent)

    req_SLAP['requestData']['pickingLog'] = PL
    PL = simplify_raw_PL(PL)
    inst_o['PICKING_LOG'] = PL

    cleanup_save(inst_o, inst_name, req_SLAP, PATH_OUT0)

    inst_name_int += 1



    # break


#
# '''Parameters needed for logging'''
# name_instance_int = 0  # needed cuz log is npy
#
#
#
# with open('./utils_benchmarking/req_template_SLAP.json', 'r') as f:
#     req_SLAP = json.load(f)
#
#

