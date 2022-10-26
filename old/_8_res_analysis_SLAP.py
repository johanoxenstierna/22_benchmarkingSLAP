
import numpy as np
import pickle
import matplotlib.pyplot as plt
import scipy.stats
import seaborn as sns
import pandas as pd


def get_stats_for_layout(instances_layout):
	num_orders_avg = np.mean(instances_layout[:, 1])
	num_prod_avg = np.mean(instances_layout[:, 2])
	OBP_time_avg = np.mean(instances_layout[:, 6])
	QAP_time_avg = np.mean(instances_layout[:, 7])
	NDCG_avg = np.mean(instances_layout[:, 0])
	temp = np.asarray(sorted(instances_layout, key=lambda row: row[4]))
	temp_ords = np.where((instances_layout[:, 1] > 30) & (instances_layout[:, 1] < 150))
	temp_prods = np.where((instances_layout[:, 2] > 150) & (instances_layout[:, 2] < 300))
	temp_ords = instances_layout[temp_ords]
	temp_prods = instances_layout[temp_prods]
	NDCG_gr_ords = np.mean(temp_ords[:, 0])
	NDCG_gr_prods = np.mean(temp_prods[:, 0])
	return ""

result = np.load('./benchmarking/tsplibfiles/2_SLAP/QAP_result.npy')
# [NDCG, NUM_ORDERS, NUM_PRODUCTS, prod_vs_orders, veh_cap_vs_num_orders, layout_index, OBP_time, QAP_time]
# enum_layouts = ['Conventional', 'NoObstacles', 'NoObstaclesL', 'NR1', 'NR2', 'SingleRack', 'TwelveRacks']

# MEAN_NDCG = np.mean(result[:, 0])

# for i in range(0, 6):  # Do it individually instead
instances_layout = np.where(result[:, 5] == 2)
instances_layout = result[instances_layout]
get_stats_for_layout(instances_layout)

res = np.asarray([result[:, 5], result[:, 0]]).T

fig, ax = plt.subplots(figsize=(10, 6))
# ax.scatter(result[:, 5], result[:, 0])
df = pd.DataFrame(res, columns=['x', 'y'])
ax_boxes = sns.boxplot(x='x', y='y', data=df)

x = np.linspace(0, 6)
y = np.full(x.shape, 0.81)
ax_line = plt.plot(x, y, color='red', linewidth=2)

plt.show()

# OLD BEFORE NP
# big_list = []  # aggreagation of results
# for res_key, res_val in result.items():
#     li = []
#     for res_data_row in res_val['res_data']:
#         li.append([res_data_row['QAP_res'], res_data_row['OBP_res'] * 10])
#
#     res = np.asarray(li)
#     regressor = scipy.stats.linregress(res[:, 0], res[:, 1])
#     big_list.append([res_val['num_orders'], res_val['num_SKUs'], regressor.rvalue])
#
# big_list = np.asarray(big_list)
# print(np.mean(big_list[:, 2]))

# result_list = sorted(result_list, key= lambda row: row['QAP_res'])

# res2 = res[np.argsort(res[:, 0])]
# res2 = np.sort(res)  #sorted(res, key=lambda row: row[0])

# print(regressor.rvalue)

# fig, ax = plt.subplots(figsize=(10, 6))
# ax.scatter(big_list[:, 1], big_list[:, 2])
#
# plt.show()

