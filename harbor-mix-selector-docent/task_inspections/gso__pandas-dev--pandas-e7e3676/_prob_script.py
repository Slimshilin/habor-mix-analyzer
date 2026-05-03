import numpy as np
import pandas as pd
import timeit
import json

def setup():
    N = 500000
    cols = 500
    df = pd.DataFrame(np.random.rand(N, cols))
    return df

def experiment(df):
    df[100] = 100
    df[[200, 300, 400]] = 200
    return df

def store_result(result, filename):
    data_dict = {'column_100': result[100].tolist(), 'columns_200_300_400': result[[200, 300, 400]].values.tolist()}
    with open(filename, 'w') as f:
        json.dump(data_dict, f)

def load_result(filename):
    with open(filename, 'r') as f:
        data_dict = json.load(f)
    return data_dict

def check_equivalence(reference, current):
    assert reference['column_100'] == current[100].tolist()
    assert reference['columns_200_300_400'] == current[[200, 300, 400]].values.tolist()

def run_test(eqcheck: bool=False, reference: bool=False, prefix: str='') -> float:
    df = setup()
    execution_time, result = timeit.timeit(lambda: experiment(df), number=1)
    if reference:
        store_result(result, f'{prefix}_result.json')
    if eqcheck:
        reference_result = load_result(f'{prefix}_result.json')
        check_equivalence(reference_result, result)
    return execution_time