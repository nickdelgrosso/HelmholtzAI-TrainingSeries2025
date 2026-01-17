

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
import time
from uuid import uuid4
from types import SimpleNamespace


import numpy as np


class Runners(SimpleNamespace):
    """Runs code and measures elapsed time."""

    @staticmethod
    def run(executor, task, *args, **kwargs):
        start_wall = time.perf_counter()  # measure wall time
        process = executor(task, *args, **kwargs)
        wall = time.perf_counter() - start_wall
        return {'wall': wall, 'process': process}



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
        with ProcessPoolExecutor(max_workers=8) as ex:
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
            x += i * 10 + 5.2
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



if __name__ == "__main__":

    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=['cpu', 'io', 'numpy'] )
    parser.add_argument('execution', choices=['serial', 'threads', 'multiprocessing'] )
    args = parser.parse_args()

    tasks = {
        'cpu':   (Tasks.cpu_task,   dict(n_batches=8, n_items=3_000_000)), 
        'io':    (Tasks.io_task,    dict(n_batches=8, n_items=200)),
        'numpy': (Tasks.numpy_task, dict(n_batches=8, n_items=1500)),
    }
    executors = {
        'serial': Executors.serial, 
        'threads': Executors.threaded, 
        'multiprocessing': Executors.multiprocess,
    }
    
    times = Runners.run( executors[args.execution], tasks[args.task][0], **tasks[args.task][1])
    
    result = {'task': args.task, 'execution': args.execution, 'wall': round(times['wall'], 3), 'process': round(times['process'], 3)}
    result["OMP_NUM_THREADS"] = os.environ.get("OMP_NUM_THREADS", "Not Set")
    result["MKL_NUM_THREADS"] = os.environ.get("MKL_NUM_THREADS", "Not Set")
    result["OPENBLAS_NUM_THREADS"] = os.environ.get("OPENBLAS_NUM_THREADS", "Not Set")
    result['id'] = uuid4().hex[:8]
    
    print(json.dumps(result))



