# Using CProfile and Snakeviz to Explore Your Code's Performance.

## Background

When working on larger Python programs, it is often unclear which parts of the code are responsible for most of the runtime. Simple timing measurements can indicate that a program is slow, but they do not explain where time is being spent across different functions and modules. The built-in cProfile module addresses this by collecting function-level execution statistics for an entire program run. Used together with visualization tools such as snakeviz, these statistics provide a structured overview of how time flows through a program. This makes cProfile and snakeviz useful as exploratory tools for understanding performance at the program level, especially when applied to complete scripts or entry points rather than small code fragments.

## Reference 

### From the Command Line

| Command                                              | Description                                            |
| ---------------------------------------------------- | ------------------------------------------------------ |
| `python -m cProfile script.py`                       | Run a script under the profiler and print text output  |
| `python -m cProfile -o out.prof script.py`           | Run a script and save profiling data to a file         |
| `python -m cProfile -o out.prof -m module`           | Profile a module run via `python -m`                   |
| `python -m cProfile -o out.prof script.py arg1 arg2` | Profile a script with command-line arguments           |
| `python -m cProfile -s cumulative script.py`         | Profile and sort the outputs by cumulative time        |
| `snakeviz out.prof`                                  | Visualize profiling results interactively in a browser |


### From Inside Python


```python
import cProfile

prof = cProfile.Profile()
prof.enable()

my_function()

prof.disable()
prof.dump_stats("profile.prof")
```