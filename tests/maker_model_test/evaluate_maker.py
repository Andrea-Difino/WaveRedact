import pandas as pd
import numpy as np
import ast

results = pd.read_csv("./test_result.csv")

points = 0

for i,row in results.iterrows():
    test_ids = np.array(ast.literal_eval((row["test_ids"])))
    real_ids = np.array(ast.literal_eval((row["real_ids"])))

    if test_ids.size < real_ids.size:
        continue
    
    set_diff = np.setdiff1d(real_ids, test_ids)

    if len(set_diff) == 0:
        points += 1

print("Score of the model: " + str(points) + f"/{len(results)}")
