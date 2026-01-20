
from abc import ABC
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import json
import math
import os
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any, Callable, NewType, Optional, Protocol, ParamSpec
from uuid import uuid4

import numpy as np
import psutil

P = ParamSpec("P")

class Executor(Protocol):
    n_repeats: int

    def __call__(self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs):
        raise NotImplementedError()



def run_benchmark(task: Callable, executor: Executor, *args, **kwargs):
    """Runs code and measures elapsed time."""
    proc = psutil.Process()
    start_io = proc.io_counters()
    proc.cpu_percent(interval=None)  # initialize cpu utilization interval
    start_wall = time.perf_counter()  # measure wall time
    process = executor(task, *args, **kwargs)
    wall = time.perf_counter() - start_wall
    cpu_percent = proc.cpu_percent(interval=None)
    end_io = proc.io_counters()
    return {
        'wall': wall, 
        'process': process, 
        'cpu_percent': cpu_percent,
        'io_read_count': end_io.read_count - start_io.read_count,
        'io_read_bytes': end_io.read_bytes - start_io.read_bytes,
        'io_read_rate': (end_io.read_bytes - start_io.read_bytes) / wall,
        'io_write_count': end_io.write_count - start_io.write_count,
        'io_write_bytes': end_io.write_bytes - start_io.write_bytes,
        'io_write_rate': (end_io.write_bytes - start_io.write_bytes) / wall,
    }


JSON = None | bool | int | float | str | list["JSON"] | dict[str, "JSON"]


@dataclass
class Serial:
    n_repeats: int

    def __call__(self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> Any:
        start_cpu = time.process_time()
        for _ in range(self.n_repeats):
            task(*args, **kwargs) 
        cpu_time = time.process_time() - start_cpu
        return cpu_time


class Executors(SimpleNamespace):
    
    @staticmethod
    def serial(task, n_batches, n_items):
        "1 CPU, One at a time."
        start_cpu = time.process_time()
        for _ in range(n_batches):
            task(n=n_items)  # don't need process time of task, it's roughly equivalent to the total process time here.
        cpu_time = time.process_time() - start_cpu
        return cpu_time
            
    @staticmethod
    def threaded(task, n_batches, n_items):
        "Using Python Threads."
        start_cpu = time.process_time()
        with ThreadPoolExecutor(max_workers=8) as ex:
            list(ex.map(task, [n_items] * n_batches ))  # Don't use process time from individual threads; not meaningful.
        cpu_time = time.process_time() - start_cpu
        return cpu_time

    @staticmethod
    def multiprocess(task, n_batches, n_items):
        "Using Multiprocessing."
        host_cpu_start_time = time.process_time()
        with ProcessPoolExecutor(max_workers=4) as ex:
            cpu_times = list(ex.map(task, [n_items] * n_batches ))  # Need the individual process times.

        host_cpu_time = time.process_time() - host_cpu_start_time
        return sum(cpu_times) + host_cpu_time





class Tasks(SimpleNamespace):

    @staticmethod
    def cpu_task(n):
        """A CPU-Bound task--no real memory usage, no waiting."""
        start_cpu = time.process_time()
        x = 0
        for i in range(n):
            x += math.sqrt(i * 10 + 5.2)
        return time.process_time() - start_cpu

    @staticmethod
    def io_task(n):
        """An IO-Bound task--just waiting."""
        start_cpu = time.process_time()
        for i in range(n):
            time.sleep(0.000001)
        return time.process_time() - start_cpu

    @staticmethod
    def numpy_task(n):
        """A CPU-Bound task done out-of-Python."""
        start_cpu = time.process_time()
        a = np.random.rand(n, n)
        b = np.random.rand(n, n)
        np.matmul(a, b)
        return time.process_time() - start_cpu



def run_benchmark_as_subprocess(
        entry_point: str, 
        params: dict[str, JSON] | None = None,
        env: Optional[dict[str, str]] = None,
        python: str = sys.executable,
    ):
    
    params_json = json.dumps(params) if params else None
    out = subprocess.run(
        [python, __file__, entry_point],
        input=params_json,
        env=os.environ | (env if env else {}),
        check=False, text=True, capture_output=True,
    )
    if out.returncode != 0:
        print(out.stderr)
        raise RuntimeError()
    
    return out.stdout


def cli():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("entrypoint", help='The import path to the function to be run (e.g. "package.module:fun")')
    parser.add_argument("--params", help="JSON params for the entrypoint, or '-' to read from stdin", default="{}")
    args = parser.parse_args()

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
            print("error: expected Expected input on stdin.")
            parser.error("expected JSON on stdin (when using '--params -')")
        
        json_params = sys.stdin.read()
        print('stdin:', json_params)
    else:
        json_params = args.params

    
    params = json.loads(json_params)

    ## Validate Params go with Entry Point, using type signature
    import inspect
    sig = inspect.signature(task_function)
    try:
        sig.bind(**params)
    except TypeError as e:
        parser.error(f"Invalid parameters for {task_function.__name__}: {json_params}")
    
    ## Run the benchmark!
    run_benchmark(
        task=task_function, 
        executor=Serial(n_repeats=10),
    )
    
    
    



if __name__ == "__main__":

    
    cli()
    

    # measurements = Runners.run( executors[args.execution], tasks[args.task][0], **tasks[args.task][1])
    
    # result = {'task': args.task, 'execution': args.execution} | measurements
    # result["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS", "Not Set")
    # result["MKL_NUM_THREADS"] = os.environ.get("MKL_NUM_THREADS", "Not Set")
    # result["OPENBLAS_NUM_THREADS"] = os.environ.get("OPENBLAS_NUM_THREADS", "Not Set")
    # result['id'] = uuid4().hex[:8]
    
    # print(json.dumps(result))



