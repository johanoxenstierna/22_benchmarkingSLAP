import json
import requests

# PATH0 = './req_SLAP.json'
# PATH0 = './c12_5627.json'
# PATH0 = './c11_fb1d.json'
PATH0 = './c11_fb1d_AFT.json'
# PATH0 = './c232_47f6_AFT.json'
# PATH0 = './c55_222b_AFT.json'
# PATH0 = './c460_d01a_AFT.json'

PATH_RELOC_EFFORT = './send_one_res.json'

with open(PATH0, 'r') as f:
    req = json.load(f)

with open(PATH_RELOC_EFFORT, 'r') as f:
    R = json.load(f)
    R = R['R']

PL = req['requestData']['pickingLog']

dist_tot = 0
for _, req_pro in PL.items():
    req_pro['_meta']['save_in_gui_test'] = True
    req_pro['_meta']['warehouse']['tag'] = req['_meta']['warehouse']['tag']
    req_pro['requestType'] = 'pickroute'
    response_raw = requests.post('http://localhost:8080/' + req_pro['requestType'],
                                 json.dumps(req_pro),
                                 headers={'Content-type': 'application/json'})

    res = json.loads(response_raw.text)
    dist_tot += res['responseData']['optimalRouteDistance']

print("dist PRO: " + str(dist_tot) + " R: " + str(R) + "  tot: " + str(dist_tot + R))