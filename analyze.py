

import os
import json

# PATH = './EROSKI/SLAP/data7_500f/'
PATH = './EROSKI/SLAP/processedData/data7_500f/'

_, _, files = os.walk(PATH).__next__()

pros = {}
'''build pros'''
for file_name in files:

    with open(PATH + file_name, 'r') as f:
        pro = json.load(f)
    pros[file_name] = pro


# # If there are duplicate data ====================
# num_duplicates = 0
# for pro_id0, pro0 in pros.items():
#     pickRoundId = pro0['requestData']['pickRoundId']
#     for pro_id1, pro1 in pros.items():
#         if pro_id0 == pro_id1:
#             pass
#         else:
#             if pro1['requestData']['pickRoundId'] == pickRoundId:
#                 num_duplicates += 1
# print(num_duplicates)