from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
import json
import os
import psutil
import subprocess
import sys
import time
from types import SimpleNamespace
from typing import Any, Callable, Literal, Optional, ParamSpec, Type
from uuid import uuid4


JSON = None | bool | int | float | str | list["JSON"] | dict[str, "JSON"]
P = ParamSpec("P")

class Executor(ABC):

    def __init__(self, n_repeats: int = 1) -> None:
        self.n_repeats = n_repeats

    @abstractmethod
    def __call__(self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs): ...
    

@dataclass
class Serial(Executor):
    n_repeats: int

    def __call__(self, task: Callable[P, object], *args: P.args, **kwargs: P.kwargs) -> float:
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




def run_benchmark(
        task: Callable, 
        task_params: Optional[dict[str, Any]] = None, 
        n_repeats: int = 1, 
        execution_mode: Literal['serial'] = 'serial',
    ) ->  dict[str, "JSON"]:

    """Runs code and measures elapsed time."""
    params = task_params if task_params is not None else {}
    executor_types: dict[str, Type[Executor]] = {
        'serial': Serial,
    }
    executor = executor_types[execution_mode](n_repeats=n_repeats)
    proc = psutil.Process()
    start_io = proc.io_counters()
    proc.cpu_percent(interval=None)  # initialize cpu utilization interval
    start_wall = time.perf_counter()  # measure wall time
    process = executor(task, **params)
    wall = time.perf_counter() - start_wall
    cpu_percent = proc.cpu_percent(interval=None)
    end_io = proc.io_counters()
    return {
        'run_id': uuid4().hex[:8],
        'wall': round(wall, 4),   # if the time differences are sub-millisecond, don't trust it.
        'process': round(process, 4), # if the time differences are sub-millisecond, don't trust it.
        'cpu_percent': round(cpu_percent, 1),
        'io_read_count': end_io.read_count - start_io.read_count,
        'io_read_bytes': end_io.read_bytes - start_io.read_bytes,
        'io_read_rate': round((end_io.read_bytes - start_io.read_bytes) / wall, 6),
        'io_write_count': end_io.write_count - start_io.write_count,
        'io_write_bytes': end_io.write_bytes - start_io.write_bytes,
        'io_write_rate': round((end_io.write_bytes - start_io.write_bytes) / wall, 6),
    }



"""
Special Case: Making things work for Seperate Environments Requires a Subprocess.  

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
        execution_mode: Literal['serial'] = 'serial',
        env: Optional[dict[str, str]] = None,
        python: str = sys.executable,
    ):
    
    params_json = json.dumps(params) if params else None
    args = [python, __file__, entry_point, '--nreps', str(n_repeats), '--execution_mode', execution_mode]
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
    parser.add_argument("--execution_mode", default='serial', choices=['serial'], help="how to batch up the work of the repetitions")
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

    ## Validate Params go with Entry Point, using type signature
    import inspect
    sig = inspect.signature(task_function)
    try:
        sig.bind(**params)
    except TypeError as e:
        parser.error(f"Invalid parameters for {task_function.__name__}: {json_params},\n\n{str(e)}")
    

    print()
    ## Run the benchmark!
    results = run_benchmark(
        task=task_function, 
        task_params=params,
        execution_mode=args.execution_mode,
        n_repeats=args.nreps,
    )
    result_json = json.dumps(results, indent=3 if args.pretty else None)
    print(result_json)
    
    
    
    



if __name__ == "__main__":
    cli()    



