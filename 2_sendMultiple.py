import os
import requests
import json

'''NR1 prob was done with R=0.5'''

# WAREHOUSE_TAGS = ['']

## UNSTAGE dataAFT
WAREHOUSE_TAG = 'NR1'
PATH0 = './tsplibfiles/2_SLAP_PRO/' + WAREHOUSE_TAG + '/'
OVERWRITE_RES = False  # whenever new ones GENERATED, old are deleted

_, inst_names, _ = os.walk(PATH0).__next__()
ii = 0
# inst_names = ['c20_8462']
# inst_names = ['c98_ac3d', 'c85_a9d3']
for inst_name in inst_names:

    PATH_INST = PATH0 + inst_name + '/' + inst_name + '.json'
    PATH_REQ = PATH0 + inst_name + '/' + inst_name + '_SLAP_req.json'
    PATH_OUT = PATH0 + inst_name + '/' + inst_name + '_SLAP_res.json'

    '''Overwrite resp'''
    try:
        with open(PATH_OUT, 'r') as f:
            res = json.load(f)
        if OVERWRITE_RES == False:
            continue
    except:  # if res cant be found then nothing is to be doneee
        pass

    with open(PATH_INST, 'r') as f:
        inst = json.load(f)

    with open(PATH_REQ, 'r') as f:
        req = json.load(f)

    print("sending " + inst_name)

    response_raw = requests.post('http://localhost:8080/' + req['requestType'], json.dumps(req),
                                         headers={'Content-type': 'application/json'})

    res = json.loads(response_raw.text)

    # SHOULD BE NEGATIVE
    print("distanceSaved: " + str(float(res['distanceTotalOptimized'] - res['distanceOriginal'])))

    with open(PATH_OUT, 'w') as f:  # DONT CHANGE NAME!!! rename after
        json.dump(res, f, indent=4)

    ii += 1

    # if ii > 2:
    #     break
    # break

