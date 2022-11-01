"""
Bucket URL:
https://drive.google.com/drive/folders/10v-nbemiZMVcSKnks1Y7oCUiwpBWKtcX?usp=sharing
"""

import requests
import json
import os
import random
random.seed(99)
# import EROSKI.SLAP.preprocess
# from EROSKI.SLAP.filter_pros import PickrouteFilter
# 95872 baseline according to this module using pickroute service. ___ using SLAP
# BAD locs: 2-30-11

# SEND_SLAP_REQ = 0
# USE_FILTER = 0
# SLAP_REQ_NAME = '5a.json'

# if SEND_SLAP_REQ:
#     PATH = './EROSKI/SLAP/reqs/'
#     SAVE_RESPS = 1
#     PATH_OUT = './EROSKI/SLAP/resps/'
# else:
    # PATH = './EROSKI/SLAP/processedData/data7_30f/'  # 22311
    # PATH = './EROSKI/SLAP/data7_6500/'
    # PATH_FILTER = './EROSKI/SLAP/data7_500/'
    # PATH = './EROSKI/SLAP/dataFails/'
# PATH = './TOYO/pro_resps/'

PATH = './utils_benchmarking/dataAFT/'
# PATH = 'inRequest'
# PATH_IR = './tsplibfiles/2_SLAP_PRO/NR1/c3_5e00/c3_5e00_SLAP_req.json'
# SAVE_RESPS = 0  # depr
# PATH_OUT = './TOYO/pro_resps/'
SAVE_IN_GUI_TEST = False

dont_do = ['req_1d_stopstop']
reqs = {}
if PATH == 'inRequest':  # load manually
    with open(PATH_IR, 'r') as f:
        req = json.load(f)
    reqs = req['requestData']['pickingLog']
    for pro_id, pro in req['requestData']['pickingLog'].items():
        pro['_meta']['warehouse']['tag'] = req['_meta']['warehouse']['tag']
        pro['_meta']['requestName'] = pro_id
        pro['_meta']['save_in_gui_test'] = SAVE_IN_GUI_TEST

else:  # loaded from path. Assumed to have tag and name etc (sorted out in pros_aft

    path, folders, file_names_b = os.walk(PATH).__next__()
    for file_name in file_names_b:
        with open(PATH + file_name, 'r') as f:
            req = json.load(f)

        reqs[file_name[:-5]] = req

# _pro_filter = PickrouteFilter()
total_dist = 0
dists = []
for req_id, req in reqs.items():
    # if req['requestData']['pickRoundId'] != 20220426673:
    #     continue

    # # TTETETTETMP
    # req['_meta']['save_in_gui_test'] = True
    # print(PATH + file_name)
    # req['_meta']['requestName'] = file_name[:-5]  # ASSUMED .json

    '''dont save in BQ'''
    req['_meta']['saveInBQ'] = False

    # if file_name[:-5] in dont_do:
    #     continue

    response_raw = requests.post('http://localhost:8080/' + req['requestType'], json.dumps(req),
                                 headers={'Content-type': 'application/json'})

    res = json.loads(response_raw.text)

    # if USE_FILTER:
    #     _pro_filter.add_pro(res)

    # if SAVE_RESPS:
    #     with open(PATH_OUT + file_name, 'w') as f:
    #         json.dump(res, f, indent=True)

    # else:
    dists.append(res['responseData']['optimalRouteDistance'])
    total_dist += res['responseData']['optimalRouteDistance']

print(total_dist)
# ONLY IF DATA DOES NOT INCLUDE RESPONSES (DEPR?)============
# if USE_FILTER == 1:
#     _pro_filter.filter_on_dist_and_num_skus()
#     _pro_filter.write_filtered_pros(PATH_FILTER)
# print("distanceSaved: " + str(res['distanceSaved']))
adf = 5



