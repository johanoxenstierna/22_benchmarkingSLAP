import os
import requests
import json

PATH = './TOYO-W/req_0_TW30AFT.json'
PATH = './TOYO-W/req_0_TW30.json'
# PATH = './TOYO/SLAP/req_temp.json'
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