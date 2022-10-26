
"""
Extract pros based on distance / num_picks. Run from send_req.py.
Lowest scores gets eliminated
If pro is dist is 100 but only has 1 pick, it gets 100 score.
If pro is dist is 100 and has 50 picks, it gets 2 score.
If pro is dist 10 and has 1 pick, it gets 10 score.
If pro is dist 10 and has 50 pick, it gets 0.2 score.
"""

import json

class PickrouteFilter:

    def __init__(_s):
        _s.pros = []  # cuz its gonna be sorted
        _s.pros_keys = []
        _s.NUM_TO_KEEP = 500

    def add_pro(_s, res):
        """res: response"""
        # if res['_meta']['requestName'] in _s.pros_keys:
        #     raise Exception("request already in _s.pros and should be impossible")

        _s.pros.append(res)
        # _s.pros_keys.append(res['_meta']['requestName'])

    def filter_on_dist_and_num_skus(_s):
        """Extract pros based on distance / num_picks.
        The ones with lowest score are eliminated (already well slotted)."""
        for i, pro in enumerate(_s.pros):
            dist = pro['responseData']['optimalRouteDistance']
            num_skus = len(pro['responseData']['picksInfo']['SKUs'])
            pro['responseData']['slottingScore'] = dist / num_skus

        _s.pros.sort(key=lambda x: x['responseData']['slottingScore'], reverse=True)

        NUM_TO_REMOVE = len(_s.pros) - _s.NUM_TO_KEEP
        for _ in range(NUM_TO_REMOVE):
            _s.pros.pop()

        aa = 5

    def write_filtered_pros(_s, PATH):
        """"""
        for i, pro in enumerate(_s.pros):
            with open(PATH + str(i) + '.json', 'w') as f:
                json.dump(pro, f, indent=True)







