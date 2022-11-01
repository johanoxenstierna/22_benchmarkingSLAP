import os
import requests
import json

# PATH = './EROSKI/pro_unidirectional/5a_orig.json'
# PATH = './c6_07c7.json'
# PATH = './c12_5627.json'
# PATH = './c170_8f37.json'
# PATH = './reqs/c55_222b.json'
# PATH = './c460_d01a_AFT.json'
# PATH = './c232_47f6.json'
# PATH = './c232_47f6_AFT.json'
# PATH = './TOYO/SLAP/0_pl.json'
# PATH = './TOYO/SLAP/1_emptyLocs.json'
# PATH = './tsplibfiles/2_SLAP_PRO/NoObstacles/c6_07c7/c6_07c7_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/NoObstacles/c170_8f37/c170_8f37_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/NoObstacles/c55_222b/c55_222b_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/NoObstacles/c460_d01a/c460_d01a_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/NR1/c3_5e00/c3_5e00_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/TwelveRacks/c23_45e0/c23_45e0_SLAP_req.json'
# PATH = './tsplibfiles/2_SLAP_PRO/TwelveRacks/c97_5406/c97_5406_SLAP_req.json'
PATH = './utils_benchmarking/req_reassignmentPath.json'
# PATH = './utils_benchmarking/req_temp.json'

with open(PATH, 'r') as f:
    req = json.load(f)

response_raw = requests.post('http://localhost:8080/' + req['requestType'], json.dumps(req),
                                     headers={'Content-type': 'application/json'})

res = json.loads(response_raw.text)

with open('send_one_res.json', 'w') as f:  # DONT CHANGE NAME!!! rename after
    json.dump(res, f, indent=4)

aa = 5