import numpy as np


PATH = './benchmarking/results5minSMDSmatrix.npy'

res = np.load(PATH)

col0 = res[:, 0]

indicies = col0.argsort()
res_s = res[indicies]
aa = 6