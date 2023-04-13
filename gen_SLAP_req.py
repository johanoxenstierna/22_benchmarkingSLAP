
'''From requests/resps in folder'''
import os
import json

PATH = './TOYO-W/'
# PATH_REQS = './TOYO-W/pros30/'
PATH_REQS = './utils_benchmarking/dataAFT/'
PATH_OUT = PATH + 'req_0_TW30AFT.json'

_, _, file_names = os.walk(PATH_REQS).__next__()

with open('./req_SLAP.json', 'r') as f:
    req = json.load(f)

PL = {}
for file_name in file_names:

    with open(PATH_REQS + file_name, 'r') as f:
        req_pro = json.load(f)

    PL[file_name] = req_pro

req['requestData']['pickingLog'] = PL
req['requestData']['origin'] = "TOYO-W_START"
req['requestData']['destination'] = "TOYO-W_START"


req['_meta']['warehouse']['tag'] = 'TOYO-W'
req['_meta']['saveInBQ'] = False

req['_meta']['optimizationParameters'] = {
    "NUM_ITERATIONS": 30000,
    "USE_REASSIGNMENT_DISTANCE": True,
    "PERC_SWAPS": 100,
    "C1": 6,
    "C2": 1,
    "R_AMOUNT": 0.5,
    "MAX_LOCATION_CHANGES": 30
}

with open(PATH_OUT, 'w') as f:
    json.dump(req, f, indent=True)

adf = 5