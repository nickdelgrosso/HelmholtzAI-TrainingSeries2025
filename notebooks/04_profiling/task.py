
import math
import time
def cpu_task(n):
    """A CPU-Bound task--no real memory usage, no waiting."""
    x = 0
    for i in range(n):
        x += math.sqrt(i * 10 + 5.2)


def slow_executor(task, n_repeats):
    start_cpu = time.process_time()
    for _ in range(n_repeats):
        time.sleep(.01)
        task()
    return time.process_time() - start_cpu
