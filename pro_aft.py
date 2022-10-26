"""This module takes a SLAP response and converts SKUs locations in pickruns in a
specified folder to the new locations provided in the response."""


import json
import os
from copy import deepcopy

PATH_SLAP_RESP = 'send_one_res_biasTest3.json'
# PATH_PRO_BEF = 'c232_47f6.json'
PATH_PRO_BEF = './c11_fb1d.json'
# PATH_PRO_BEF = 'c460_d01a.json'
# PATH_PRO_AFT = 'c232_47f6_AFT.json'
PATH_PRO_AFT = './c11_fb1d_AFT.json'
# PATH_PRO_AFT = 'c460_d01a_AFT.json'

'''SLAP result response'''
with open(PATH_SLAP_RESP, 'r') as f:
    res = json.load(f)

'''Load in pro befs before slapping'''
with open(PATH_PRO_BEF, 'r') as f:
    req = json.load(f)

PL_bef = req['requestData']['pickingLog']
PL_aft = deepcopy(PL_bef)

'''conduct swaps in data'''
dones = []
for swapper_id, swapper in res['SKUsSlotted'].items():

    '''Swap'''
    for pr_id_a, pr_a in PL_aft.items():

        pr_a['_meta']['start_depot_idx'] = 0
        pr_a['_meta']['end_depot_idx'] = 1

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

'''Export. Redump but with new PL'''
req['requestData']['pickingLog'] = PL_aft
with open(PATH_PRO_AFT, 'w') as f:
    req = json.dump(req, f, indent=True)


aa = 5




