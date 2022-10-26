

"""Just a script to add empty locs to a request given a locKeyInd and a pickingLog.
They cannot already exist in the pickingLog"""

import json
import random

def empty_locations(req_SLAP, tsplib_parent, NUM_EMPTY_LOCATIONS, TYPE=None, locsList=None):


    # TYPE = 'bench'
    # PATH_REQ_W_PL = './tsplibfiles/2_SLAP_PRO/NoObstacles/c6_07c7/c6_07c7_SLAP_req.json'
    # NUM_TO_ADD = 2

    empty_locs = []

    if TYPE == 'bench':
        # PATH_TSPLIB_PARENT = './tsplibfiles/2_SLAP_PRO/NoObstacles/tsplib_parent.json'
        # with open(PATH_TSPLIB_PARENT, 'r') as f:
        #     tsplibparent = json.load(f)
        locsList = list(range(2, int(tsplib_parent['num_pick_locs_warehouse'])))
        locsList = [str(x) for x in locsList]
    else:
        locsList = locsList

    # with open(PATH_REQ_W_PL, 'r') as f:
    #     req = json.load(f)
    pL = req_SLAP['requestData']['pickingLog']

    locs_already_used = []
    for pro_id, pro in pL.items():
        for loc in pro['requestData']['picksInfo']['locations']:
            if loc not in locs_already_used:
                locs_already_used.append(loc)

    for _ in range(NUM_EMPTY_LOCATIONS):
        fl_found = False
        loc_cand = None
        while fl_found == False:
            loc_cand = random.choice(locsList)
            if loc_cand not in locs_already_used:
                fl_found = True

        locs_already_used.append(loc_cand)
        empty_locs.append(loc_cand)

    req_SLAP['requestData']['emptyLocations'] = empty_locs

    return req_SLAP


if __name__ == "__main__":
    PATH_REQ_W_PL = './TOYO/SLAP/1_emptyLocs.json'
    PATH_LOCKEYIND = './TOYO/SLAP/locKeyInd.json'
    NUM_EMPTY_LOCATIONS = 5


    with open(PATH_REQ_W_PL, 'r') as f:
        req = json.load(f)
    with open(PATH_LOCKEYIND, 'r') as f:
        locKeyInd = json.load(f)

    locsList = list(locKeyInd.keys())

    req2 = empty_locations(req, None, NUM_EMPTY_LOCATIONS, locsList=locsList)

    with open(PATH_REQ_W_PL, 'w') as f:
        json.dump(req, f, indent=True)




