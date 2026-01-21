"""
Example script for demonstrating cProfile and snakeviz.

This script simulates a small data-processing pipeline with:
- setup work
- disk I/O
- CPU-bound computation

Written by ChatGPT 5.2, for demonstration purposes only.
"""

import time
import math
import random
from pathlib import Path


DATA_FILE = Path("data.txt")


def generate_data(n: int):
    """Write n random numbers to disk."""
    with DATA_FILE.open("w") as f:
        for _ in range(n):
            f.write(f"{random.random()}\n")


def load_data():
    """Read numbers from disk."""
    numbers = []
    with DATA_FILE.open() as f:
        for line in f:
            numbers.append(float(line))
    return numbers


def expensive_computation(numbers):
    """CPU-bound work."""
    total = 0.0
    for x in numbers:
        total += math.sqrt(x) * math.sin(x)
    return total


def run_pipeline(n: int):
    """Main entry point."""
    generate_data(n)
    numbers = load_data()
    result = expensive_computation(numbers)
    return result


def main():
    # Simulate setup work
    time.sleep(0.2)

    result = run_pipeline(50_000)

    # Simulate teardown / logging
    time.sleep(0.1)
    print("Result:", result)


if __name__ == "__main__":
    main()
