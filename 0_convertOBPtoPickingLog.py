"""Each order becomes a pickrun"""

import os
import json
import random
from copy import deepcopy

WAREHOUSE_TAG = 'NoObstacles'
name_instance = 'c11_fb1d'
# name_instance = 'c170_8f37'
# name_instance = 'c55_222b'
# name_instance = 'c460_d01a'
# name_instance = 'c232_47f6'

PATH0 = './tsplibfiles/1_1v4/NoObstacles/instances/' + name_instance + '/'
PATH_OUT = './tsplibfiles/2_SLAP_PRO/NoObstacles/'

HERE CREATE TABLE PROTOTYPE THINK ABOUT WHICH METRICS TO USE

NUM_DUPLICATE_Os = 20
NUM_DUPLICATE_SKUs = 1


with open('./tsplibfiles/1_1v4/' + WAREHOUSE_TAG + '/tsplib_parent.json', 'r') as f:
    tsplib_parent = json.load(f)

with open(PATH0 + name_instance + '.json', 'r') as f:
    instance = json.load(f)

with open('./utils_benchmarking/req_template_SLAP.json', 'r') as f:
    req_SLAP = json.load(f)

with open('utils_benchmarking/req_template_pro.json', 'r') as f:
    req_pro_templ = json.load(f)  # deepcopy for each.

assert(instance['NAME'] == name_instance)
req_SLAP['_meta']['req_name'] = name_instance

NUM_SKUs = len(instance['VISIT_LOCATION_SECTION'])
O_keys = list(instance['ORDERS'])


'''Duplicate orders'''
order_key = len(instance['ORDERS']) + 1

'''Just some test to validate instance'''
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
reasonable baseline is to assume a random slotting policy.'''

for sku in instance['VISIT_LOCATION_SECTION']:
    loc = str(random.randint(3, tsplib_parent['NUM_LOCATIONS']) - 2)  # -2 for safety
    instance['VISIT_LOCATION_SECTION'][sku] = loc

pickingLog = {}
ii = 0  # pickingLog MUST BE ENUMERATED (could also be moved to handler.py in opt789)
for o_id, o_val in instance['ORDERS'].items():
    req_pro = deepcopy(req_pro_templ)
    # del req_pro['_meta']
    # req_pro['_meta']['warehouse']['tag'] = WAREHOUSE_TAG  # NEEDED TO SAVE IN GUI TEST
    req_pro['requestData']['pickRoundId'] = name_instance + "_" + o_id

    for sku in o_val:
        sku_loc = instance['VISIT_LOCATION_SECTION'][sku]

        req_pro['requestData']['picksInfo']['SKUs'].append(sku)
        req_pro['requestData']['picksInfo']['locations'].append(sku_loc)  # have to be set to random within num_locs

    pickingLog[ii] = req_pro
    ii += 1

req_SLAP['requestData']['pickingLog'] = pickingLog

with open('./' + name_instance + '.json', 'w') as f:
    json.dump(req_SLAP, f, indent=4)

ff = 5
