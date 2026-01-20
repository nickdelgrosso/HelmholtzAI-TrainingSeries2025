from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial
import json
import os
import threading
import psutil
import subprocess
import sys
import time
from typing import Any, Callable, Optional, Protocol
from uuid import uuid4



## Batch Executors

class BatchExecutor(Protocol):

    def __call__(self, task: Callable[[], Any], n_repeats: int) -> float: ...
    


def serial(task: Callable, n_repeats: int): 
    "1 CPU, One at a time."
    start_cpu = time.process_time()
    _ = [task() for _ in range(n_repeats)]
    cpu_time = time.process_time() - start_cpu
    return cpu_time

        
def threaded(task: Callable, n_repeats: int):
    "Using Python Threads."
    with ThreadPoolExecutor(max_workers=8) as ex:
        start_cpu = time.process_time()
        futures = [ex.submit(task) for _ in range(n_repeats)]
        _ = [future.result() for future in futures]  # not using these, but still collecting in case of raised exceptions.
    cpu_time = time.process_time() - start_cpu
    return cpu_time


def multiprocessing(task: Callable, n_repeats: int):
    "Using Multiprocessing."
    timed_task = partial(serial, task, n_repeats=1)
    with ProcessPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(timed_task) for _ in range(n_repeats)]
        child_process_times = [future.result() for future in futures]
    return sum(child_process_times)





executors: dict[str, BatchExecutor] = {
    'serial': serial,
    'threading': threaded,
    'multiprocessing': multiprocessing,
}


## Runners

JSON = None | bool | int | float | str | list["JSON"] | dict[str, "JSON"]

def run_benchmark(
        task: Callable[[], Any], 
        executor: Optional[BatchExecutor] = None,
        n_repeats: int = 1,
    ) ->  dict[str, "JSON"]:

    """Runs code and measures elapsed time."""


    # Measure Timing    
    if executor is None:
        # Single-Run Mode (unreliable for quick functions)
        start_wall = time.perf_counter()  # measure wall time
        start_process = time.process_time()  # measure wall time
        task()
        process_time = time.process_time() - start_process
        wall_time = time.perf_counter() - start_wall
    else:
        # Batch Mode (run many times to get better estimates)
        start_wall = time.perf_counter()  # measure wall time
        process_time = executor(task, n_repeats=n_repeats)
        wall_time = time.perf_counter() - start_wall
    
    
    time_metrics = {
        'wall': round(wall_time, 4),   # if the time differences are sub-millisecond, don't trust it.
        'process': round(process_time, 4), # if the time differences are sub-millisecond, don't trust it.
        'effective_cpu_utilization': round(process_time / wall_time, 2),
    }

    # Measure IO
    proc = psutil.Process()
    start_io = proc.io_counters()
    proc.cpu_percent(interval=None)  # initialize cpu utilization interval
    task()
    end_io = proc.io_counters()


    io_metrics = {
        'read_count': end_io.read_count - start_io.read_count,
        'read_bytes': end_io.read_bytes - start_io.read_bytes,
        'read_rate': round((end_io.read_bytes - start_io.read_bytes) / wall_time, 6),
        'write_count': end_io.write_count - start_io.write_count,
        'write_bytes': end_io.write_bytes - start_io.write_bytes,
        'write_rate': round((end_io.write_bytes - start_io.write_bytes) / wall_time, 6),
    }

    # Measure Memory (Sampling Method)
    sampling_interval_secs = .01
    proc = psutil.Process()
    stop = threading.Event()
    peak_rss = 0
    def sample_memory_use():
        nonlocal peak_rss
        while not stop.is_set():
            try:
                peak_rss = max(peak_rss, proc.memory_info().rss)
            except psutil.Error:
                pass
            time.sleep(sampling_interval_secs)
    t = threading.Thread(target=sample_memory_use, daemon=True)
    t.start()
    try:
        task()
    finally:
        stop.set()
        t.join()

    memory_metrics = {
        'peak_observed_rss_mb': round(peak_rss / (1024 ** 2), 2)
    }


    all_metrics = {
        'id': uuid4().hex[:8],
        'time': time_metrics,
        'io': io_metrics,
        'memory': memory_metrics,
    }

    return all_metrics



"""
Special Case: Making things work for New Environments Requires the benchmark is run in a seperate process.

The code below allows use of `run_benchmark()` through a CLI, (entry point for subprocessing),
which itself can be called from `run_benchmark_as_subprocess()` (entry point if using from python).

This is a bit convoluted, I know, but it makes it easy to experiment with environment variables, 
needed for learning about performance tweaking of numpy and such libraries.

For this to work, the function to be benchmarked needs to be in an importable module.
If calling from a notebook, you can use the `%%writefile` cell magick to make it without leaving the module.
"""

def run_benchmark_as_subprocess(
        entry_point: str, 
        params: dict[str, JSON] | None = None,
        n_repeats: int = 1,
        executor_entry_point: str = 'serial',
        env: Optional[dict[str, str]] = None,
        python: str = sys.executable,
    ):
    
    params_json = json.dumps(params) if params else None
    args = [python, __file__, entry_point, '--nreps', str(n_repeats), '--executor', executor_entry_point]
    if params_json:
        args.extend(['--params', '-'])
    
    out = subprocess.run(
        args,
        input=params_json,
        env=os.environ | (env if env else {}),
        check=False, text=True, capture_output=True,
    )
    if out.returncode != 0:
        print(out.stderr)
        raise RuntimeError()
    
    output = json.loads(out.stdout)
    return output


def cli(args=None):

    
    import argparse

    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("entrypoint", help='The import path to the function to be run (e.g. "package.module:fun")')
    parser.add_argument("--params", help="JSON params for the entrypoint, or '-' to read from stdin", default="{}")
    parser.add_argument("--nreps", default=1, type=int, help="how many repetitions to run the task")
    parser.add_argument("--executor", default='serial', help=f"The path to the batch executor function, or {set(executors.keys())}")
    parser.add_argument("--pretty", action="store_true", help="pretty-prints the JSON output")
    args = parser.parse_args(args=args)

    ## Validate Entrypoint
    import importlib
    try:
        module_path, function_name = args.entrypoint.split(":", 1)
    except ValueError:
        parser.error("Invalid entry point format.  Expected 'package.module:function'")
    
    module = importlib.import_module(module_path)
    task_function = getattr(module, function_name)
    
    ## Validate Params
    import json
    
    if args.params == '-':
        if sys.stdin.isatty():
            print("error: expected Expected input on stdin.", file=sys.stderr)
            parser.error("expected JSON on stdin (when using '--params -')")
        
        json_params = sys.stdin.read()
    else:
        json_params = args.params

    
    params = json.loads(json_params)
    task = partial(task_function, **params)

    ## Validate Params go with Entry Point, using type signature
    import inspect
    sig = inspect.signature(task_function)
    try:
        sig.bind(**params)
    except TypeError as e:
        parser.error(f"Invalid parameters for {task_function.__name__}: {json_params},\n\n{str(e)}")
    

    ## Get Batch Executor
    executor = executors.get(args.executor, None)
    if executor is None:
        try:
            module_path, function_name = args.executor.split(":", 1)
        except ValueError:
            parser.error(f"Invalid executor format.  Expected 'package.module:function' or {set(executors.keys())}")
        module = importlib.import_module(module_path)
        executor = getattr(module, function_name)

    ## Run the benchmark!
    
    results = run_benchmark(
        task=task, 
        executor=executor,
        n_repeats=args.nreps,
    )
    result_json = json.dumps(results, indent=3 if args.pretty else None)
    print(result_json)
    
    
    
    



if __name__ == "__main__":
    cli()    



