"""
OBS SKUs may share the same location!

"""

import os
from pathlib import Path
import shutil
import json
import random
random.seed(7)
from copy import deepcopy
from utils_benchmarking.utils import *
from utils_benchmarking import empty_locations

# WAREHOUSE_TAG = 'TwelveRacks'
WAREHOUSE_TAG = 'NR1'
# WAREHOUSE_TAG = 'NoObstacles'

# name_instance = 'c6_07c7'  # NoO
# name_instance = 'c11_fb1d'
# name_instance = 'c170_8f37'
# name_instance = 'c55_222b'
# name_instance = 'c460_d01a'
# name_instance = 'c232_47f6'

name_instance = 'c3_5e00'  # 12

# name_instance = 'c6_1e43'
# name_instance = 'c23_45e0'  # Twelve
# name_instance = 'c97_5406'  # Twelve

PATH0 = './tsplibfiles/1_1v4/' + WAREHOUSE_TAG + '/instances/' + name_instance + '/'
PATH_OUT0 = './tsplibfiles/2_SLAP_PRO/' + WAREHOUSE_TAG + '/'
SAVE = 1

'''Parameters to modify instance'''
NUM_EMPTY_LOCATIONS = 1
NUM_DUPLICATE_Os = 0
NUM_DUPLICATE_SKUs = 0
NUM_EXTRA_SKUs_IN_PROS = (0, 0) # used to make pickruns longer. Num skus in so many pros

'''Parameters needed for logging'''
name_instance_int = 0  # needed cuz log is npy

with open('./tsplibfiles/1_1v4/' + WAREHOUSE_TAG + '/tsplib_parent.json', 'r') as f:
    tsplib_parent = json.load(f)

with open(PATH0 + name_instance + '.json', 'r') as f:
    instance = json.load(f)

with open('./utils_benchmarking/req_template_SLAP.json', 'r') as f:
    req_SLAP = json.load(f)

with open('utils_benchmarking/req_template_pro.json', 'r') as f:
    req_pro_templ = json.load(f)  # deepcopy for each.

assert(instance['NAME'] == name_instance)
req_SLAP['_meta']['requestName'] = name_instance
req_SLAP['_meta']['warehouse']['tag'] = WAREHOUSE_TAG
req_SLAP['_meta']['bench'] = {'req_name_int': name_instance_int}
req_SLAP['_meta']['bench'] = {'req_name_int': name_instance_int}

req_SLAP['_meta']['optimizationParameters'] = {
    "NUM_ITERATIONS": 100,
    "USE_REASSIGNMENT_DISTANCE": True,
    "PERC_SWAPS": 100,
    "C1": 2,
    "C2": 1,
    "R_AMOUNT": 0.5
}

req_SLAP['_meta']['bench']['ALGO'] = None

# NUM_SKUs = len(instance['VISIT_LOCATION_SECTION'])
O_keys = list(instance['ORDERS'])

'''Duplicate orders BEFORE ADDING EXTRA SKUs ================================'''
order_key = len(instance['ORDERS']) + 1

# Validate instance
keys = list(instance['ORDERS'].keys())
if max([int(x) for x in keys]) >= order_key:
    raise Exception("INSTANCE ERROR")

Os_duplicated = []
for _ in range(NUM_DUPLICATE_Os):

    '''select orders randomly'''
    fl_found_o = False
    while fl_found_o == False:
        o_key0 = random.choice(O_keys)
        if o_key0 not in Os_duplicated:
            fl_found_o = True

    instance['ORDERS'][str(order_key)] = deepcopy(instance['ORDERS'][o_key0])
    instance['NUM_VISITS'] += len(instance['ORDERS'][o_key0])

    order_key += 1

# ===================================

'''Add extra SKUs to some orders. Mainly to give Concorde a chance'''
Os_extended = []
for _ in range(NUM_EXTRA_SKUs_IN_PROS[1]):  # select order randomly

    '''select two diff orders randomly'''
    fl_found_o = False
    o_key0 = None
    while fl_found_o == False:
        o_key0 = random.choice(O_keys)
        if o_key0 not in Os_extended:
            fl_found_o = True

    Os_extended.append(o_key0)

    for _ in range(NUM_EXTRA_SKUs_IN_PROS[0]):  # select sku randomly
        sku = str(random.randint(3, tsplib_parent['num_pick_locs_warehouse']))
        instance['ORDERS'][o_key0].append(sku)

        if sku in instance['VISIT_LOCATION_SECTION']:
            # sku_loc = instance['VISIT_LOCATION_SECTION'][sku]
            pass
        else:  # need to add it to VISIT_LOCATION_SECTION
            sku_loc = str(random.randint(3, tsplib_parent['num_pick_locs_warehouse']))
            instance['VISIT_LOCATION_SECTION'][sku] = sku_loc  # may be duplicates

adf = 5



# =====================================================

'''Duplicate SKUs (service should be capable of working with it)
even if it doesnt make use of it'''

for _ in range(NUM_DUPLICATE_SKUs):

    '''select two diff orders randomly'''
    o_key0 = random.choice(O_keys)
    o_key1 = random.choice(O_keys)
    while o_key1 == o_key0:  # select different order
        o_key1 = random.choice(O_keys)

    fl_found_two_skus = False
    attempts = 0
    while fl_found_two_skus == False:
        sku0 = random.choice(instance['ORDERS'][o_key0])
        if sku0 not in instance['ORDERS'][o_key1]:
            instance['ORDERS'][o_key1].append(sku0)
            instance['NUM_VISITS'] += 1
            fl_found_two_skus = True
        else:
            attempts += 1

        if attempts > 50:
            print("ADf")
            break

# =============================================================

'''Generate new random locations in instance. In OBP these are assumed to be 
well-slotted according to some logic. But when the purpose is slotting itself, the only 
reasonable baseline is to assume a random slotting policy. Although multiple skus per loc supported, 
for bench its easier to just have 1 per loc, hence pop.'''

locs_p = list(range(1, tsplib_parent['num_pick_locs_warehouse'] - 2))
random.shuffle(locs_p)

for sku in instance['VISIT_LOCATION_SECTION']:
    loc = locs_p.pop()
    instance['VISIT_LOCATION_SECTION'][sku] = str(loc)

pickingLog = {}
ii = 0  # pickingLog MUST BE ENUMERATED (could also be moved to handler.py in opt789)
for o_id, o_val in instance['ORDERS'].items():
    req_pro = deepcopy(req_pro_templ)
    # del req_pro['_meta']
    req_pro['_meta']['warehouse']['tag'] = WAREHOUSE_TAG  # NEEDED TO SAVE IN GUI TEST FOR LATER (pros) (The tag of the SLAP request is stored above)
    req_pro['requestData']['pickRoundId'] = name_instance + "_" + o_id

    for sku in o_val:
        sku_loc = instance['VISIT_LOCATION_SECTION'][sku]

        req_pro['requestData']['picksInfo']['SKUs'].append(sku)
        req_pro['requestData']['picksInfo']['locations'].append(sku_loc)  # have to be set to random within num_locs

    pickingLog[ii] = req_pro
    ii += 1

req_SLAP['requestData']['pickingLog'] = pickingLog

PL = simplify_raw_PL(pickingLog)
instance['PICKING_LOG'] = PL

if NUM_EMPTY_LOCATIONS > 0:
    req_SLAP = empty_locations.empty_locations(req_SLAP, tsplib_parent, NUM_EMPTY_LOCATIONS, TYPE='bench')

'''Modify other things in original instance'''
instance['HEADER']['COMMENTS']['descr'] = 'Modified TSPLIB instance for the SLAP'
del instance['ORDERS']
del instance['NUM_VEHICLES']
del instance['NUM_CAPACITIES']
del instance['CAPACITIES']
del instance['TIME_AVAIL_SECTION']

if SAVE:

    PATH_OUT1 = PATH_OUT0 + name_instance

    '''Remove previous folder if exists and gen new'''
    dirpath = Path(PATH_OUT1)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(PATH_OUT1)
    os.mkdir(PATH_OUT1)

    '''Save the SLAP request'''
    # aa = PATH_OUT + '/' + name_instance + '/' + name_instance
    with open(PATH_OUT1 + '/' + name_instance + '_SLAP_req.json', 'w') as f:
        json.dump(req_SLAP, f, indent=4)

    '''save the instance'''
    with open(PATH_OUT1 + '/' + name_instance + '.json', 'w') as f:
        json.dump(instance, f, indent=4)
