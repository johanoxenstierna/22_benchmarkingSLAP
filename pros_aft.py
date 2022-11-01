"""This module takes a SLAP response and converts SKUs locations in pickruns in a
specified folder to the new locations provided in the response."""


import json
import os
from copy import deepcopy

# PATH_SLAP_RESP = './TOYO/SLAP/resps/5a.json'
# PATH_SLAP_RESP = 'send_one_res.json'
PATH_SLAP_RESP = './tsplibfiles/2_SLAP_PRO/NR1/c98_ac3d/c98_ac3d_SLAP_res.json'
# PATH_SLAP_RESP = './send_one_res_biasTestOther.json'
# FILE_NAME = 'RES_5a9km.json'
# PATH_PRO_BEF = './EROSKI/SLAP/data2_4/'
# PATH_PRO_BEF = './EROSKI/SLAP/processedData/data3_18/'
# PATH_PRO_BEF = './TOYO/processedData/data7_50f/'
# PATH_PRO_BEF = './TOYO/pro_resps/'
PATH_PRO_BEF = 'inRequest'
PATH_PRO_BEF_IR = './tsplibfiles/2_SLAP_PRO/NR1/c98_ac3d/c98_ac3d_SLAP_req.json'
PATH_PRO_AFT = './utils_benchmarking/dataAFT/'
SAVE_IN_GUI_TEST = True
WAREHOUSE_TAG = 'NR1'

'''Remove previous pro files in aft'''
path, folders, file_names = os.walk(PATH_PRO_AFT).__next__()
for file_name in file_names:
    os.remove(PATH_PRO_AFT + file_name)

'''SLAP result response'''
with open(PATH_SLAP_RESP, 'r') as f:
    res = json.load(f)

'''Load in pro befs before slapping'''
pros_bef = {}
if PATH_PRO_BEF == 'inRequest':  # load manually
    # path_bef = PATH_PRO_BEF_IR
    # path_bef = './TOYO/SLAP/0_pl.json'

    with open(PATH_PRO_BEF_IR, 'r') as f:
        req = json.load(f)
    pros_bef = req['requestData']['pickingLog']
    for pro_id, pro in req['requestData']['pickingLog'].items():
        pro['_meta']['warehouse']['tag'] = WAREHOUSE_TAG
        pro['_meta']['requestName'] = pro_id

else:  # loaded from path

    path, folders, file_names_b = os.walk(PATH_PRO_BEF).__next__()
    for file_name in file_names_b:
        with open(PATH_PRO_BEF + file_name, 'r') as f:
            req = json.load(f)

        req['_meta']['save_in_gui_test'] = SAVE_IN_GUI_TEST

        pros_bef[file_name[:-5]] = req


pros_aft = deepcopy(pros_bef)

'''conduct swaps in data'''
dones = []
for swapper_id, swapper in res['slottedSKUs'].items():
    # try:
    #     swappee_id = swapper['swappedWith']
    #     swappee = res['SKUsSlotted'][swappee_id]
    # except:  # it wasn't swapped
    #     continue

    '''Swap'''
    for pr_id_a, pr_a in pros_aft.items():

        # if swapper_id in pr_a['requestData']['picksInfo']['SKUs'] and \
        #     swappee_id in pr_a['requestData']['picksInfo']['SKUs']:
        #     raise Exception("A swap within the same pickrun found")
        #
        # if swapper_id in pr_a['requestData']['picksInfo']['SKUs']:
        #     if swapper_id not in dones:
        #         swapper_numi = pr_a['requestData']['picksInfo']['SKUs'].index(swapper_id)
        #         pr_a['requestData']['picksInfo']['locations'][swapper_numi] = swapper['raw_loc_cur']
        #         dones.append(swapper_id)
        #
        # elif swappee_id in pr_a['requestData']['picksInfo']['SKUs']:
        #     if swappee_id not in dones:
        #         swappee_numi = pr_a['requestData']['picksInfo']['SKUs'].index(swappee_id)
        #         pr_a['requestData']['picksInfo']['locations'][swappee_numi] = swappee['raw_loc_cur']
        #         dones.append(swappee_id)

        for i, sku in enumerate(pr_a['requestData']['picksInfo']['SKUs']):
            if sku == swapper_id:
                raw_loc_orig = pr_a['requestData']['picksInfo']['locations'][i]
                if raw_loc_orig != swapper['rawLocOriginal']:
                    raise Exception("raw_loc_orig != swapper['rawLocOriginal'] THIS IS LIKELY BECAUSE pro_aft.py PATH_PRO_BEF IS SET UP WRONG ")
                raw_loc_cur = swapper['rawLocCurrent']
                pr_a['requestData']['picksInfo']['locations'][i] = raw_loc_cur

        aa = 5

'''make sure saveInBQ is set to false'''
for pro_id, pro in pros_aft.items():
    pro['_meta']['saveInBQ'] = False
    pro['_meta']['save_in_gui_test'] = SAVE_IN_GUI_TEST

'''Export'''
for pro_id, pro in pros_aft.items():
    # for file_name in file_names_b:
    with open(PATH_PRO_AFT + pro_id + '.json', 'w') as f:
        req = json.dump(pro, f, indent=True)


aa = 5




