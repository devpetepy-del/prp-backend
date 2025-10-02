import time

def start_time() -> float:
    start = time.perf_counter()
    return start

def calculate_time(start):
    duration = time.perf_counter() - start
    print(f"View took {duration:.4f} seconds")