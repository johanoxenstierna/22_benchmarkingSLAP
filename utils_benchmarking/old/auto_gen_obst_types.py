import random


def coordinate_obstacle_control(obstacles_all, x_cand, y_cand):
	for key_obs in obstacles_all:
		obs_corners = obstacles_all[key_obs]['corners']
		x_le = obs_corners[0][0]
		x_ri = obs_corners[3][0]  # OBS ASSUMES RECTANGLES
		y_do = obs_corners[0][1]
		y_up = obs_corners[1][1]

		if (x_cand >= x_le and x_cand <= x_ri) and (y_cand >= y_do and y_cand <= y_up):
			return False

	return True


def empty_placeholders(NUM):

	x_lo = 10
	x_hi = 75
	y_lo = 10
	y_hi = 75
	allowed_coords = []
	for i in range(NUM):
		coord_cand = [random.randint(x_lo, x_hi), random.randint(y_lo, y_hi)]
		if coord_cand not in allowed_coords:
			allowed_coords.append(coord_cand)

	return {}, [], [], allowed_coords


def SingleRack(NUM_LOCS):
	"""
	HARDCODED
	"""

	obs_all = {"1": {
			"corners": [[10, 10], [10, 60], [12, 60], [12, 10]],
			"inds": []}}

	allowed_coords = []
	x_lo = 14
	x_hi = 78
	y_lo = 3
	y_hi = 78

	for i in range(NUM_LOCS):  # OBS if you change this number it becomes impossible to reproduce tsplib
		coord_cand = [random.randint(x_lo, x_hi), random.randint(y_lo, y_hi)]
		if coord_cand not in allowed_coords:
			if (coord_cand[0] > 9 and coord_cand[0] < 13) and (coord_cand[1] > 9 and coord_cand[1] < 61):
				pass  # failed
			else:
				allowed_coords.append(coord_cand)

	return obs_all, [], [], allowed_coords


def TwelveRacks(NUM_LOCS):
	"""
		HARDCODED
		"""
	obs_all = {
		"1": {
			"corners": [[10, 10], [10, 30], [12, 30], [12, 10]],
			"inds": []
			},
		"2": {
			"corners": [[16, 10], [16, 30], [18, 30], [18, 10]],
			"inds": []
			},
		"3": {
			"corners": [[22, 10], [22, 30], [24, 30], [24, 10]],
			"inds": []
			},
		"4": {
			"corners": [[10, 36], [10, 56], [12, 56], [12, 36]],
			"inds": []
			},
		"5": {
			"corners": [[16, 36], [16, 56], [18, 56], [18, 36]],
			"inds": []
			},
		"6": {
			"corners": [[22, 36], [22, 56], [24, 56], [24, 36]],
			"inds": []
			},
		"7": {
			"corners": [[60, 10], [60, 30], [62, 30], [62, 10]],
			"inds": []
			},
		"8": {
			"corners": [[66, 10], [66, 30], [68, 30], [68, 10]],
			"inds": []
			},
		"9": {
			"corners": [[72, 10], [72, 30], [74, 30], [74, 10]],
			"inds": []
			},
		"10": {
			"corners": [[60, 36], [60, 56], [62, 56], [62, 36]],
			"inds": []
			},
		"11": {
			"corners": [[66, 36], [66, 56], [68, 56], [68, 36]],
			"inds": []
			},
		"12": {
			"corners": [[72, 36], [72, 56], [74, 56], [74, 36]],
			"inds": []
			}
	}

	allowed_coords = []
	x_lo = 3
	x_hi = 78
	y_lo = 3
	y_hi = 78

	for i in range(NUM_LOCS):
		coord_cand = [random.randint(x_lo, x_hi), random.randint(y_lo, y_hi)]
		if coord_cand not in allowed_coords:
			if coordinate_obstacle_control(obs_all, coord_cand[0], coord_cand[1]) is True and (coord_cand[0] < 26 or coord_cand[0] > 57):
				allowed_coords.append(coord_cand)
			else:
				pass  # failed

	return obs_all, [], [], allowed_coords


def Conventional(DEBUGGING=False):  # horizontally aligned
	"""
	Number of locations is totally hardcoded in here
	All locations are allowed. This is to ensure instances are more varied (there are only 220 locations)
	Returns
	-------

	"""
	obs_all = {}
	allowed = []
	allowed_coords = []  # NEW

	# LOWER RACKS -----------
	x_cur = 10
	y_low = 10
	y_high = 30

	for i in range(1, 12):  # generates 11
		# obs_all[str(i)] = {}
		obs = [[x_cur, y_low], [x_cur, y_high], [x_cur+2, y_high], [x_cur+2, y_low]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed.append({'x_lo': x_cur - 1, 'x_hi': x_cur - 1, 'y_lo': y_low, 'y_hi': y_high})
		allowed.append({'x_lo': x_cur + 3, 'x_hi': x_cur + 3, 'y_lo': y_low, 'y_hi': y_high})
		for y_c in range(y_low, y_high):  # new
			if y_c % 4 == 0:
				allowed_coords.append([x_cur - 1, y_c])
				allowed_coords.append([x_cur + 3, y_c])
		x_cur += 6

	if DEBUGGING == False:
		# UPPER RACKS -----------
		x_cur = 10
		y_low = 40
		y_high = 60

		for i in range(12, 23):  # generates 11
			# obs_all[str(i)] = {}
			obs = [[x_cur, y_low], [x_cur, y_high], [x_cur+2, y_high], [x_cur+2, y_low]]
			obs_all[str(i)] = {"corners": obs, "inds": []}
			allowed.append({'x_lo': x_cur - 1, 'x_hi': x_cur - 1, 'y_lo': y_low, 'y_hi': y_high})
			allowed.append({'x_lo': x_cur + 3, 'x_hi': x_cur + 3, 'y_lo': y_low, 'y_hi': y_high})
			for y_c in range(y_low, y_high):  # new
				if y_c % 4 == 0:
					allowed_coords.append([x_cur - 1, y_c])
					allowed_coords.append([x_cur + 3, y_c])
			x_cur += 6


	forbidden = None

	return obs_all, forbidden, allowed, allowed_coords


def NR1():
	obs_all = {}
	allowed_regs = []
	allowed_coords = []  # NEW added CUZ otherwise there'll be lots of misses in empty land

	# LOWER RACKS -----------
	x_cur = 10
	y_low = 10
	y_high = 30

	for i in range(1, 12):  # generates 11
		obs = [[x_cur, y_low], [x_cur, y_high], [x_cur + 2, y_high], [x_cur + 2, y_low]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed_regs.append({'x_lo': x_cur - 1, 'x_hi': x_cur - 1, 'y_lo': y_low, 'y_hi': y_high})
		allowed_regs.append({'x_lo': x_cur + 3, 'x_hi': x_cur + 3, 'y_lo': y_low, 'y_hi': y_high})
		for y_c in range(y_low, y_high):  # new
			if y_c % 4 == 0:
				allowed_coords.append([x_cur - 1, y_c])
				allowed_coords.append([x_cur + 3, y_c])

		x_cur += 6

	# UPPER RACKS -----------
	x_lo = 10
	x_hi = 50
	y_cur = 40

	for i in range(12, 18):  #
		obs = [[x_lo, y_cur], [x_lo, y_cur + 2], [x_hi, y_cur + 2], [x_hi, y_cur]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed_regs.append({'x_lo': x_lo, 'x_hi': x_hi, 'y_lo': y_cur + 3, 'y_hi': y_cur + 3})
		allowed_regs.append({'x_lo': x_lo, 'x_hi': x_hi, 'y_lo': y_cur - 3, 'y_hi': y_cur - 3})

		for x_c in range(x_lo, x_hi):  # new
			if x_c % 4 == 0:
				allowed_coords.append([x_c, y_cur + 3])
				allowed_coords.append([x_c, y_cur - 1])

		y_cur += 6

	forbidden = None
	print("num allowed_coords: " + str(len(allowed_coords)))
	return obs_all, forbidden, allowed_regs, allowed_coords


def NR2():
	obs_all = {}
	allowed_regs = []
	allowed_coords = []  # NEW added CUZ otherwise there'll be lots of misses in empty land

	# LOWER RACKS -----------
	x_cur = 15
	y_low = 10
	y_high = 30

	for i in range(1, 11):  # generates 11
		obs = [[x_cur, y_low], [x_cur, y_high], [x_cur + 2, y_high], [x_cur + 2, y_low]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed_regs.append({'x_lo': x_cur - 1, 'x_hi': x_cur - 1, 'y_lo': y_low, 'y_hi': y_high})
		allowed_regs.append({'x_lo': x_cur + 3, 'x_hi': x_cur + 3, 'y_lo': y_low, 'y_hi': y_high})
		for y_c in range(y_low, y_high):  # new
			if y_c % 4 == 0:
				allowed_coords.append([x_cur - 1, y_c])
				allowed_coords.append([x_cur + 3, y_c])

		x_cur += 6

	# UPPER RACKS 1-----------
	x_lo = 5
	x_hi_cur = 30
	y_cur = 40

	for i in range(len(obs_all) + 1, len(obs_all) + 7):  #
		obs = [[x_lo, y_cur], [x_lo, y_cur + 2], [x_hi_cur, y_cur + 2], [x_hi_cur, y_cur]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed_regs.append({'x_lo': x_lo, 'x_hi': x_hi_cur, 'y_lo': y_cur + 3, 'y_hi': y_cur + 3})
		allowed_regs.append({'x_lo': x_lo, 'x_hi': x_hi_cur, 'y_lo': y_cur - 3, 'y_hi': y_cur - 3})

		for x_c in range(x_lo, x_hi_cur):  # new
			if x_c % 4 == 0:
				allowed_coords.append([x_c, y_cur + 3])
				allowed_coords.append([x_c, y_cur - 1])

		y_cur += 6
		x_hi_cur += 1

	# UPPER RACKS 2 -----------
	x_lo_cur = 40
	x_hi = 75
	y_cur = 40

	for i in range(len(obs_all) + 1, len(obs_all) + 7):  #
		obs = [[x_lo_cur, y_cur], [x_lo_cur, y_cur + 2], [x_hi, y_cur + 2], [x_hi, y_cur]]
		obs_all[str(i)] = {"corners": obs, "inds": []}
		allowed_regs.append({'x_lo': x_lo_cur, 'x_hi': x_hi, 'y_lo': y_cur + 3, 'y_hi': y_cur + 3})
		allowed_regs.append({'x_lo': x_lo_cur, 'x_hi': x_hi, 'y_lo': y_cur - 3, 'y_hi': y_cur - 3})

		for x_c in range(x_lo_cur, x_hi):  # new
			if x_c % 4 == 0:
				allowed_coords.append([x_c, y_cur + 3])
				allowed_coords.append([x_c, y_cur - 1])

		y_cur += 6
		x_lo_cur += 1

	forbidden = None

	return obs_all, forbidden, allowed_regs, allowed_coords
