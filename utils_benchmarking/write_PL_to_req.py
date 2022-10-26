import os
import json

PATH_PL = './TOYO/pro_resps/'
PATH_REQ = './TOYO/SLAP/0_pl.json'

with open(PATH_REQ, 'r') as f:
    req = json.load(f)

req['requestData']['assignmentOptions']['evaluationData'] = 'pickingLogInRequest'

PL = {}
path, folders, file_names_b = os.walk(PATH_PL).__next__()
# ii = 5
for i, file_name in enumerate(file_names_b):
# for file_name in file_names_b:
    with open(PATH_PL + file_name, 'r') as f:
        pro_req = json.load(f)
    PL[str(i)] = pro_req

req['requestData']['pickingLog'] = PL

with open(PATH_REQ, 'w') as f:
    json.dump(req, f, indent=4)



