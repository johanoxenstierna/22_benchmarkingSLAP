

import json

PATH_RESP = './send_one_res_30.json' # RENAME IT! send_one_res MIGHT BE OVERWRITTEN using send_one
# PATH_RESP = './tsplibfiles/2_SLAP_PRO/NR1/c57_91eb/c57_91eb_SLAP_res.json' # RENAME IT! send_one_res MIGHT BE OVERWRITTEN using send_one
PATH_OUT = './utils_benchmarking/req_reassignmentPath.json'
WAREHOUSE_TAG = 'TOYO-W'
ORIGIN = "TOYO-W_START" #"WH_STARTSTOP0_1"  #
DESTINATION = "TOYO-W_START"#"WH_STARTSTOP0_1"  #
SAVE_IN_GUI_TEST = False


with open(PATH_RESP, 'r') as f:
    resp = json.load(f)

with open('./utils_benchmarking/req_template_pro.json', 'r') as f:
    req = json.load(f)

req['_meta']['save_in_gui_test'] = SAVE_IN_GUI_TEST
req['_meta']['warehouse']['tag'] = WAREHOUSE_TAG
req['_meta']['requestName'] = 'reassignment path'

req['requestData']['picksInfo']['locations'] = resp['reassignmentPath']
req['requestData']['picksInfo']['SKUs'] = [str(i) for i in range(len(resp['reassignmentPath']))]
req['requestData']['origin'] = ORIGIN
req['requestData']['destination'] = DESTINATION


with open(PATH_OUT, 'w') as f:
    req = json.dump(req, f, indent=True)