import random
random.seed(4)

SKUs_all = {
    'a': {
        'raw_loc_orig': '5',
        'raw_loc_cur': '4',
    },
    'b': {
        'raw_loc_orig': '2',
        'raw_loc_cur': '3'
    },
    'c': {
        'raw_loc_orig': '3',
        'raw_loc_cur': '6'
    },
    'd': {
        'raw_loc_orig': '4',
        'raw_loc_cur': '1'
    },
    'e': {
        'raw_loc_orig': '1',
        'raw_loc_cur': '5'
    },
    'f': {
        'raw_loc_orig': '6',
        'raw_loc_cur': '2'
    },
}

s0_ids = list(SKUs_all.keys())
random.shuffle(s0_ids)
s0_l_origs = [SKUs_all[x]['raw_loc_orig'] for x in s0_ids]

_r_ids = [s0_ids.pop()]
_r_l_origs = [s0_l_origs.pop()]

fl_last_added = False
while fl_last_added == False:
    cur_id = _r_ids[-1]
    next_l = SKUs_all[cur_id]['raw_loc_cur']

    if next_l in s0_l_origs and next_l in _r_l_origs:
        raise Exception("next cant be in both lists")

    if next_l in s0_l_origs:
        index = s0_l_origs.index(next_l)
        _r_l_origs.append(s0_l_origs.pop(index))
        _r_ids.append(s0_ids.pop(index))

    elif next_l in _r_l_origs:
        '''means that its a cycle (double, triplet, quadruple etc)'''
        index = _r_l_origs.index(next_l)

        _r_l_origs.append(_r_l_origs[index])
        _r_ids.append(_r_ids[index])

        _r_l_origs.append(s0_l_origs.pop())
        _r_ids.append(s0_ids.pop())  # then start at new randomly selected

    else:
        raise Exception("next in seq could not be found")

    '''exit clause for when last added and it needs to go to its cur loc, 
    which is somewhere in list.'''
    if len(s0_ids) < 1:
        cur_id = _r_ids[-1]
        last_l = SKUs_all[cur_id]['raw_loc_cur']

        if last_l not in _r_l_origs:
            raise Exception("last connection cant be made")

        index = _r_l_origs.index(last_l)
        _r_l_origs.append(_r_l_origs[index])
        _r_ids.append(_r_ids[index])
        fl_last_added = True

    adf = 5

print(_r_ids)
print(_r_l_origs)
adf = 5




