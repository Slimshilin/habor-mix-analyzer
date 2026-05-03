import numpy as np
import pandas as pd
import timeit
import json


def setup():
    """Setup the data for the experiment."""
    # Create a DataFrame with random data
    N = 500_000
    cols = 500
    df = pd.DataFrame(np.random.rand(N, cols))
    return df


def experiment(df):
    """Perform the setitem operation on the DataFrame."""
    # Perform the setitem operation
    df[100] = 100
    df[[100, 200, 300]] = 100
    return df


def store_result(result, filename):
    """Store the result of the experiment."""
    # Serialize the DataFrame to JSON
    result_dict = {
        "columns": result.columns.tolist(),
        "data": result.iloc[:, [100, 200, 300]].to_dict(orient="list"),
    }
    with open(filename, "w") as f:
        json.dump(result_dict, f)


def load_result(filename):
    """Load the reference result from a file."""
    with open(filename, "r") as f:
        result_dict = json.load(f)
    return result_dict


def check_equivalence(reference, current):
    """Check if the current result is equivalent to the reference result."""
    # Check columns
    assert reference["columns"] == current.columns.tolist()
    # Check data for specific columns
    for col in [100, 200, 300]:
        assert reference["data"][str(col)] == current[col].tolist()


def run_test(eqcheck: bool = False, reference: bool = False, prefix: str = "") -> float:
    """Run the performance and equivalence test."""
    # Setup the experiment data
    df = setup()

    # Time the experiment
    execution_time, result = timeit.timeit(lambda: experiment(df), number=1)

    # Store the result if reference is True
    if reference:
        store_result(result, f"{prefix}_result.json")

    # Check equivalence if eqcheck is True
    if eqcheck:
        reference_result = load_result(f"{prefix}_result.json")
        check_equivalence(reference_result, result)

    return execution_time


timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Measure performance of API.")
    parser.add_argument(
        "output_file", type=str, help="File to append timing results to."
    )
    parser.add_argument(
        "--eqcheck", action="store_true", help="Enable equivalence checking"
    )
    parser.add_argument(
        "--reference",
        action="store_true",
        help="Store result as reference instead of comparing",
    )
    parser.add_argument(
        "--file_prefix",
        type=str,
        help="Prefix for any file where reference results are stored",
    )
    args = parser.parse_args()

    # Measure the execution time
    execution_time = run_test(args.eqcheck, args.reference, args.file_prefix)

    # Append the results to the specified output file
    with open(args.output_file, "a") as f:
        f.write(f"Execution time: {execution_time:.6f}s\n")


if __name__ == "__main__":
    main()


timeit.template = """
def inner(_it, _timer{init}):
    {setup}
    _t0 = _timer()
    for _i in _it:
        retval = {stmt}
    _t1 = _timer()
    return _t1 - _t0, retval
"""


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Measure performance of API.')
    parser.add_argument('output_file', type=str, help='File to append timing results to.')
    parser.add_argument('--eqcheck', action='store_true', help='Enable equivalence checking')
    parser.add_argument('--reference', action='store_true', help='Store result as reference instead of comparing')
    parser.add_argument('--file_prefix', type=str, help='Prefix for any file where reference results are stored')
    args = parser.parse_args()

    # Measure the execution time
    execution_time = run_test(args.eqcheck, args.reference, args.file_prefix)

    # Append the results to the specified output file
    with open(args.output_file, 'a') as f:
        f.write(f'Execution time: {execution_time:.6f}s\n')

if __name__ == '__main__':
    main()
