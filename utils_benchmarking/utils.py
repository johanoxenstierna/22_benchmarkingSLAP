
import os
import json
import random
from copy import deepcopy
from pathlib import Path
import shutil

def init_SLAP_req(WAREHOUSE_TAG, inst_name, inst_name_int,
                  inst_o):
    """inst_o: instance old"""

    with open('./utils_benchmarking/req_template_SLAP.json', 'r') as f:
        req_SLAP = json.load(f)

    assert (inst_o['NAME'] == inst_name)
    req_SLAP['_meta']['requestName'] = inst_name
    req_SLAP['_meta']['warehouse']['tag'] = WAREHOUSE_TAG
    req_SLAP['_meta']['bench'] = {'req_name_int': inst_name_int}

    return req_SLAP

def duplicate_orders(inst_o, NUM_DUPLICATE_Os, O_keys):
    '''Duplicate orders BEFORE ADDING EXTRA SKUs ================================'''
    order_key = len(inst_o['ORDERS']) + 1

    # Validate instance
    keys = list(inst_o['ORDERS'].keys())
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

        inst_o['ORDERS'][str(order_key)] = deepcopy(inst_o['ORDERS'][o_key0])
        inst_o['NUM_VISITS'] += len(inst_o['ORDERS'][o_key0])

        order_key += 1


def add_extra_SKUs(inst_o, NUM_EXTRA_SKUs_IN_PROS,
                   O_keys, tsplib_parent):
    '''Add extra SKUs to some orders. Mainly to give Concorde a chance'''

    Os_extended = []
    if inst_o['NAME'] == 'c17_a4be':
        adf = 5
    num_orders = min(len(O_keys), NUM_EXTRA_SKUs_IN_PROS[1])  # cant add skus to orders which dont exist

    for _ in range(num_orders):  # select order randomly

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
            inst_o['ORDERS'][o_key0].append(sku)

            if sku in inst_o['VISIT_LOCATION_SECTION']:
                # sku_loc = instance['VISIT_LOCATION_SECTION'][sku]
                pass
            else:  # need to add it to VISIT_LOCATION_SECTION
                sku_loc = str(random.randint(3, tsplib_parent['num_pick_locs_warehouse']))
                inst_o['VISIT_LOCATION_SECTION'][sku] = sku_loc  # may be duplicates

    aa = 5

def duplicate_SKUs(inst_o, NUM_DUPLICATE_SKUs, O_keys):
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
            sku0 = random.choice(inst_o['ORDERS'][o_key0])
            if sku0 not in inst_o['ORDERS'][o_key1]:
                inst_o['ORDERS'][o_key1].append(sku0)
                inst_o['NUM_VISITS'] += 1
                fl_found_two_skus = True
            else:
                attempts += 1

            if attempts > 50:
                print("ADf")
                break


def gen_req_PL_and_random_locs(inst_o, inst_name, WAREHOUSE_TAG, tsplib_parent):
    '''Generate new random locations in instance. In OBP these are assumed to be
    well-slotted according to some logic. But when the purpose is slotting itself, the only
    reasonable baseline is to assume a random slotting policy. Although multiple skus per loc supported,
    for bench its easier to just have 1 per loc, hence pop.
    The loaded req is just for pro.'''

    with open('utils_benchmarking/req_template_pro.json', 'r') as f:
        req_pro_templ = json.load(f)  # deepcopy for each.

    locs_p = list(range(1, tsplib_parent['num_pick_locs_warehouse'] - 2))
    random.shuffle(locs_p)

    for sku in inst_o['VISIT_LOCATION_SECTION']:
        loc = locs_p.pop()
        inst_o['VISIT_LOCATION_SECTION'][sku] = str(loc)

    pickingLog = {}
    ii = 0  # pickingLog MUST BE ENUMERATED (could also be moved to handler.py in opt789)
    for o_id, o_val in inst_o['ORDERS'].items():
        req_pro = deepcopy(req_pro_templ)
        # del req_pro['_meta']
        req_pro['_meta']['warehouse'][
            'tag'] = WAREHOUSE_TAG  # NEEDED TO SAVE IN GUI TEST FOR LATER (pros) (The tag of the SLAP request is stored above)
        req_pro['requestData']['pickRoundId'] = inst_name + "_" + o_id

        for sku in o_val:
            sku_loc = inst_o['VISIT_LOCATION_SECTION'][sku]

            req_pro['requestData']['picksInfo']['SKUs'].append(sku)
            req_pro['requestData']['picksInfo']['locations'].append(sku_loc)  # have to be set to random within num_locs

        pickingLog[ii] = req_pro
        ii += 1

    return pickingLog


def simplify_raw_PL(PL_raw):
    PL = {}

    for pro_id, pro in PL_raw.items():

        PL[pro_id] = {}
        PL[pro_id]['LOCATIONS'] = pro['requestData']['picksInfo']['locations']
        PL[pro_id]['SKUS'] = pro['requestData']['picksInfo']['SKUs']

    return PL


def cleanup_save(inst_o, inst_name, req_SLAP, PATH_OUT0):
    '''Modify other things in original instance'''
    inst_o['HEADER']['COMMENTS']['descr'] = 'Modified TSPLIB instance for the SLAP'
    del inst_o['ORDERS']
    del inst_o['NUM_VEHICLES']
    del inst_o['NUM_CAPACITIES']
    del inst_o['CAPACITIES']
    del inst_o['TIME_AVAIL_SECTION']

    PATH_OUT1 = PATH_OUT0 + inst_name

    '''Remove previous folder if exists and gen new'''
    dirpath = Path(PATH_OUT1)
    if dirpath.exists() and dirpath.is_dir():
        shutil.rmtree(PATH_OUT1)
    os.mkdir(PATH_OUT1)

    '''Save the SLAP request'''
    # aa = PATH_OUT + '/' + name_instance + '/' + name_instance
    with open(PATH_OUT1 + '/' + inst_name + '_SLAP_req.json', 'w') as f:
        json.dump(req_SLAP, f, indent=4)

    '''save the instance'''
    with open(PATH_OUT1 + '/' + inst_name + '.json', 'w') as f:
        json.dump(inst_o, f, indent=4)