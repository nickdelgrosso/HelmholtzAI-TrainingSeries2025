
import math
def cpu_task(n):
    """A CPU-Bound task--no real memory usage, no waiting."""
    x = 0
    for i in range(n):
        x += math.sqrt(i * 10 + 5.2)

