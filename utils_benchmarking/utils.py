


def simplify_raw_PL(PL_raw):
    PL = {}

    for pro_id, pro in PL_raw.items():

        PL[pro_id] = {}
        PL[pro_id]['LOCATIONS'] = pro['requestData']['picksInfo']['locations']
        PL[pro_id]['SKUS'] = pro['requestData']['picksInfo']['SKUs']

    return PL