

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

x = np.random.randint(10, 50, size=1000)
y = x + np.random.randint(1, 25, 1000)

ax1 = sns.lineplot(x=x, y=y, label='2-5 s')

plt.show()