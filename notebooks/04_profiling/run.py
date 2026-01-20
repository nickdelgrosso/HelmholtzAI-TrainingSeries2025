from benchmark_tool import run_benchmark_as_subprocess
import sys

print(run_benchmark_as_subprocess('task:cpu_task', params=dict(n=5)))
