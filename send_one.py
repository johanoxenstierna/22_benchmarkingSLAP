import os
import requests
import json

PATH = './EROSKI/pro_unidirectional/5a_orig.json'
# PATH = './c6_07c7.json'
# PATH = './c12_5627.json'
PATH = './c11_fb1d.json'
# PATH = './c170_8f37.json'
# PATH = './c55_222b.json'
# PATH = './c460_d01a_AFT.json'
# PATH = './c232_47f6.json'
# PATH = './c232_47f6_AFT.json'


with open(PATH, 'r') as f:
    req = json.load(f)

response_raw = requests.post('http://localhost:8080/' + req['requestType'], json.dumps(req),
                                     headers={'Content-type': 'application/json'})

res = json.loads(response_raw.text)

with open('./send_one_res.json', 'w') as f:
    json.dump(res, f, indent=4)

aa = 5